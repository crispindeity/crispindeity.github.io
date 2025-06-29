---
title: (JPA) Persistable
date: 2025-06-28 11:00:00 +0900
modified: 2025-06-28 11:00:00 +0900
categories:
  - JPA
  - Persistable
tags:
  - JPA
pin: false
---

## 📝 작성 배경
`Spring Data JPA` 를 사용하면서 다양한 `primary key` 생성 전략이 있는데, 이런 전략들을 사용하지 않고 직접 `ID` 값을 지정해주는 방식을 사용하는 경우도 종종 있는데 직접 `ID` 를 지정해서 사용하는 경우 발생할 수 있는 상황에 대한 주의점 및 개선 방법에 대해 간략하게 정리해보자 한다.

`Spring Data JPA` 를 사용하면서 `ID` 값을 주로 직접 지정할 때 필자는 주로 `UUID` 나 `Snowflake` 등의 형식을 사용하고 있다. 이 두가지 방식 외에도 직접 `ID` 를 지정해주는 경우에는 모두 발생할 수 있는 상황이니, 참고해보면 좋을것 같다.

---
## 👓 선 3줄 요약
- `Spring Data JPA` 에서 `ID` 를 직접 지정하면 의도치 않은 `SELECT` 쿼리가 추가로 발생함.
- `Persistable` 인터페이스 구현으로 `isNew()` 로직을 직접 제어하여 불필요한 쿼리 제거 가능.
- `BaseEntity`에 `Persistable`을 구현하면 모든 엔티티에서 일관성 있게 처리 가능.

---

## 🔍️ 예제 상황
특정 서비스에서 `User` 데이터를 저장할때 `Sequence` 나 `AutoIncrement` 를 활용하여 식별자(ID) 값을 지정하는게 아니라 여러 이유로 인해 회사에서 지정한 식별자 지정 방식을 사용해야 한다고 가정해보자.

### 아이디 생성 위임
```kotlin
@Entity
@Table(name = "users")
class UserEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0L,
    @Column(nullable = false)
    val username: String,
    @Column(nullable = false)
    val password: String
)

interface UserRepository : JpaRepository<UserEntity, Long>
```
예제를 위해 간단하게 `UserEntity` 를 위와 같이 만들었다. 학습할때 많이 사용하는 식별자 생성 전략인 `GenerationType.IDENTITY` 를 설정한 모습이다.

```kotlin
@DataJpaTest
class PersistableTest {
    @Autowired
    private lateinit var entityManager: TestEntityManager

    @Autowired
    private lateinit var userRepository: UserRepository
    
    @Test
    @DisplayName("아이디 생성을 위임 했을때")
    fun generatedValueTest() {
        val stats: Statistics =
            entityManager.entityManager
                .unwrap(Session::class.java)
                .sessionFactory
                .statistics.also {
                    it.isStatisticsEnabled = true
                    it.clear()
                }

        val entity = UserEntity(username = "test_user", password = "1234")
        userRepository.save(entity)
        userRepository.flush()

        val queryCount: Long = stats.prepareStatementCount
        println("Query Count: $queryCount")

        Assertions.assertThat(queryCount).isGreaterThanOrEqualTo(1)
    }
}
```
간단한 테스트 코드를 통해 아이디 생성을 위임한 상황에서 `save` 를 했을때 `query` 가 몇번 발생하는지 알아보자.

```text
Hibernate: 
    insert 
    into
        users
        (password, username, id) 
    values
        (?, ?, default)
Query Count: 1
```
로그를 살펴보면 `insert` 쿼리만 딱 한번 발생한걸 볼 수 있다.

대개 `Spring Data JPA` 를 활용해서 학습할때 아이디 생성을 위임하는 식으로 학습을 하기 때문에 이 부분에 대해서는    
많은 분들이 알고 있는 내용일것 같다. 그럼 이번에는 아이디 생성을 위임하는 전략을 사용하지 않고, 직접 설정해 주는 방식을 사용해보자.

### 아이디 직접 생성
```kotlin
@Entity
@Table(name = "users")
class UserEntity(
    @Id
    // @GeneratedValue(strategy = GenerationType.IDENTITY) 해당 부분을 주석 처리 또는 삭제
    val id: Long = 0L,
    @Column(nullable = false)
    val username: String,
    @Column(nullable = false)
    val password: String
)

interface UserRepository : JpaRepository<UserEntity, Long>
```
식별자 생성을 위임하던 방식에서 생성 전략을 나타내는 `Annotation` 을 주석 처리한 모습

```kotlin
@DataJpaTest
class PersistableTest {
    @Autowired
    private lateinit var entityManager: TestEntityManager

    @Autowired
    private lateinit var userRepository: UserRepository
    
    @Test
    @DisplayName("Persistable 구현하지 않았을때")
    fun nonPersistableTest() {
        val stats: Statistics =
            entityManager.entityManager
                .unwrap(Session::class.java)
                .sessionFactory
                .statistics.also {
                    it.isStatisticsEnabled = true
                    it.clear()
                }

        // UserEntity() 를 생성해 줄 때 ID 값을 직접 설정해주고 있는 모습
        val entity = UserEntity(id = 1L, username = "test_user", password = "1234")
        userRepository.save(entity)
        userRepository.flush()

        val queryCount: Long = stats.prepareStatementCount
        println("Query Count: $queryCount")

        Assertions.assertThat(queryCount).isGreaterThanOrEqualTo(2)
    }
}
```
이번에는 `UserEntity` 을 식별자를 직접 설정해보자.

```text
Hibernate: 
    select
        ue1_0.id,
        ue1_0.password,
        ue1_0.username 
    from
        users ue1_0 
    where
        ue1_0.id=?
Hibernate: 
    insert 
    into
        users
        (password, username, id) 
    values
        (?, ?, ?)
Query Count: 2
```
로그를 살펴보면, 쿼리가 2번 발생한걸 볼 수 있다. `insert` 쿼리 외에 `select` 쿼리가 추가로 발생한 모습.   
`insert` 쿼리가 한번만 발생할거라 생각했는데, 뜬금없이 `select` 쿼리가 추가로 발생한 모습이다.

먼저 왜 이런 상황이 발생하는지 간단하게 알아보고 넘어가자.

우선 이 부분을 이해하려면 `Spring Data JPA` 에서 `save()` 메서드가 내부적으로 어떻게 동작하지는 이해를 해야 한다.
`Spring Data JPA` 에서 `save()` 메서드를 직접 구현하는게 아니라 구현 되어 있는걸 그대로 사용한다면 `JpaRepositoryImplementation` 를 구현하고 있는 구현체인 `SimpleJpaRepository` 의 `save()` 메서드를 사용하게  
되는데 해당 메서드는 아래와 같이 작성되어 있다.

```kotlin
@Repository
@Transactional(readOnly = true)
public class SimpleJpaRepository<T, ID> implements JpaRepositoryImplementation<T, ID> {
    private final EntityManager entityManager;
    
    // ...
    
    @Override
	@Transactional
	public <S extends T> S save(S entity) {

		Assert.notNull(entity, ENTITY_MUST_NOT_BE_NULL);

		if (entityInformation.isNew(entity)) {
			entityManager.persist(entity);
			return entity;
		} else {
			return entityManager.merge(entity);
		}
	}
	
	// ...
}
```
여기서 우리는 3가지를 중점적으로 봐야 한다.
1. `entityInformante.isNew(entity)`
2. `entityManager.persist(entity)`
3. `entityManager.merge(entity)`

우선 첫번째 `entityInformante.isNew(entity)` 을 살펴보자.  
`isNew()` 메서드의 경우는 `JpaEntityInformationSupport` 를 상속하고 있는   
`JpaMetamodelEntityInformation` 에 있는 `isNew()` 메서드를 사용하고 있는데   
해당 메서드는 아래와 같이 작성되어 있다.

```kotlin
public class JpaMetamodelEntityInformation<T, ID> extends JpaEntityInformationSupport<T, ID> {
    // ...
    @Override
	public boolean isNew(T entity) {

		if (versionAttribute.isEmpty()
				|| versionAttribute.map(Attribute::getJavaType).map(Class::isPrimitive).orElse(false)) {
			return super.isNew(entity);
		}

		BeanWrapper wrapper = new DirectFieldAccessFallbackBeanWrapper(entity);

		return versionAttribute.map(it -> wrapper.getPropertyValue(it.getName()) == null).orElse(true);
	}
    // ...
}
```
먼저 여기서 `versionAttribute.isEmpty()` 인지 확인을 하게 되는데  
이건 `@Version` 을 선언한 필드가 있는지 확인하는 부분이다. 해당 내용은 `Optimistic Lock` 과 관련된 내용이라   
자세한 내용은 우선은 넘어가자. `UserEntity` 에 `@Version` 을 선언한 필드가 없으니 `isEnpty()` 는 `true` 를 반환하게 된다. `||(or)` 조건이다 보니, `if` 문 내부로 들어가게 된다. 

`if` 문 내부에서 `super.isNew(entity)` 를 호출하게 되는데, 이 경우에는 `EntityInformation` 을 구현하고 있는  
구현체인 `AbstractEntityInformation` 에 있는 `isNew()` 메서드를 호출하게 된다.  
해당 메서드는 아래와 같이 작성되어 있다.

```kotlin
public abstract class AbstractEntityInformation<T, ID> implements EntityInformation<T, ID> {

    // ...
    
	@Override
	public boolean isNew(T entity) {

		ID id = getId(entity);           // 1. id 값을 가지고 온다.
		Class<ID> idType = getIdType();

		if (!idType.isPrimitive()) {     // 2. id 값이 primitive 타입인지 reference 타입인지 확인 
			return id == null;
		}

		if (id instanceof Number n) {.   // 3. id 값이 Number instance 인지 확인
			return n.longValue() == 0L;  // 4. id 값이 0 인지 확인
		}

		throw new IllegalArgumentException(String.format("Unsupported primitive id type %s", idType));
	}
	
	// ...
}
```
해당 메서드에서 `entity` 의 `id` 값을 가져와 여러 조건에 맞는지 확인하는데 우리가 지정해준 값(1L)을 가지고 확인해보자.
1. 우리가 지정해준 값 `1L` 을 반환
2. `UserEntity` 의 `id` 는 `long` 으로 `primitive` 타입
    - 여기서 `id` 의 타입이 왜 `Long` 이 아니고 `long` 인지는 `kotlin` 에서 선언한 `Long` 타입이 `java` 로 변환되면서 어떻게 타입이 변경되는지 알고 있어야 이해가 되는 부분이다.
    - 간단하게 확인해 보고 싶다면 `intellij` 의 `kotlin` 을 `java` 로 `decompile` 하는 기능을 사용해보면 확인해 볼 수 있다.
    - 빠르게 설명해보자면 `kotlin` 에서 `java` 로 변환 될때 `type` 의 경우는 `var/val` 인지 `nullable` 인지 에 따라 타입이 결정되는데 `Non-nullable Long(val id: Long = 0L)`  의 경우는 `jvm` 에서 `type` 최적화로 인해 `long` 으로 변환되게 된다.
3. `id` 의 값은 `1L` 로 `long` 타입이기 때문에 `Number` 의 인스턴스가 맞다.
4. 이 부분 때문에 여기까지 긴 여정을 하게 되었는데, 여기서 `id` 의 값을 확인하는데, 지금 `id` 의 값은 `1L` 로 `0` 이 아니기 때문에 `false` 를 반환하게 된다.

마침내 우리는 `isNew()` 메서드가 어떤 값을 반환하는지 확인하였다. 그럼 다시 `save()` 메서드로 돌아가보자.

```kotlin
@Override
@Transactional
public <S extends T> S save(S entity) {

	Assert.notNull(entity, ENTITY_MUST_NOT_BE_NULL);

	if (entityInformation.isNew(entity)) {
		entityManager.persist(entity);
		return entity;
	} else {
		return entityManager.merge(entity);
	}
}
```
`save()` 메서드를 보면 `isNew()` 가 `false` 일때 `merge` 를 호출하도록 되어 있다.  
`persist` 와 `merge` 의 차이점은 간단하게 설명해서 `insert` 와 `select -> insert / update` 이 차이가 있다.
1. persist: insert 쿼리 동작
2. merge: select 쿼리 이후 해당 식별자에 대한 값이 있다면 update 를 없다면 insert 를 하도록 동작

위 두가지의 차이점 때문에 현재 `UserEntity` 에 `id` 값을 직접 지정해줬을때 `select` 쿼리가 추가적으로 발생하게 된 이유다.

사실 우리가 바라던 동작은 단순 `insert` 인데, 내부적으로 생각보다 복잡한 로직이 돌아가고 있으면서, 약간은 불필요하다  
생각될 수 있는 쿼리인 `select` 쿼리가 한번 더 발생한다는 부분에서 이 부분은 개선시킬 수 있는 방법은 없을지 찾아보자.

## ♻️ 개선 방안
`Spring Data JPA` 에서 `id` 를 직접 지정했을때 `select` 쿼리가 발생하지 않도록 개선 방안에 대해 알아보자.
1. `save()` 메서드를 직접 구현하여 사용한다.
2. `Spring Data JPA` 를 사용하지 않는다. ~~예?~~
3. `Persistable` 을 직접 구현한다.

필자는 3가지 정도 방법을 생각해보고 적용시켜 봤다.(혹시 개선할 수 있는 방법이 더 있다면 공유해주세요!)

우선 첫번째 방법.  
`save()` 메서드를 `Spring Data JPA` 에서 구현되어 있는 메서드를 사용하는게 아니라 내가 직접 구현해서 사용한다!  
사실 위 문제는 `save()` 메서드에서만 발생하는 문제는 아니다. `delete` 나 `update` 에서도 문제가 발생 할 수도 있다.
그리고 매번 `save()` 를 직접 구현하는건 번거로운 일이다.

두번째 방법.  
`Spring Data JPA` 를 사용하지 않는다!  
그렇다. `Spring` 에서 `DB` 를 다룰때 `Spring Data JPA` 만 있는게 아니다,   
그냥 `JPA` 를 사용해도 되고, `JDBC Template` 을 사용해도 되고 `Mybatis` 를 사용해도 된다.   
다만, 이 문제 때문에 이미 프로젝트에 적용 되어 있고, 적용하기로한 기술 자체를 바꾸는건 조금 생각해볼 여지가 있다.  
`save`, `update`, `delete` 정도만 `JDBC` 를 사용해도 되긴 한다. 이 부분은 어느정도 취향 차이가 있을것 같다.

세번째 방법.  
`save()` 에서 사용되는 메서드 들을 내가 직접 구현하여 사용하도록 한다.  
이 방법을 이야기 하기 위해 지금까지 많은 과정을 설명했다고 해도 무방하다.  
사실 이걸 의도한건지 잘 모르겠으나, `Persistable` 을 직접 구현하여 사용할 수 있다.

`Persistable` 은 아래와 같이 선언되어 있는 `interface` 다.
```kotlin
public interface Persistable<ID> {

	/**
	 * Returns the id of the entity.
	 *
	 * @return the id. Can be {@literal null}.
	 */
	@Nullable
	ID getId();

	/**
	 * Returns if the {@code Persistable} is new or was persisted already.
	 *
	 * @return if {@literal true} the object is new.
	 */
	boolean isNew();
}
```

이걸 `UserEntity` 에서 구현을 하게 되면 아래와 같이 구현할 수 있는데.
```kotlin
@Entity
@Table(name = "users")
class UserEntity(
    @Id
    // @GeneratedValue(strategy = GenerationType.IDENTITY) 해당 부분을 주석 처리 또는 삭제
    val id: Long = 0L,
    @Column(nullable = false)
    val username: String,
    @Column(nullable = false)
    val password: String
) : Persistable<Long> {
    @Transient
    private var isNew = true

    override fun isNew(): Boolean = isNew

    override fun getId(): Long? = id

    @PrePersist
    @PostLoad
    private fun markNotNew() {
        isNew = false
    }
}

interface UserRepository : JpaRepository<UserEntity, Long>
```
이렇게 구현을 하게 되면 `SimpleJpaRepository` 에서 `save()` 메서드를 호출 했을때 `isNew()` 메서드를 사용하게 되는데  
`AbstractEntityInformation` 의 `isNew()` 메서드를 호출하는게 아니라  
`JpaPersistableEntityInformation` 의 `isNew()` 메서드를 호출하게 된다.

왜 `JpaPersistableEntityInformation` 을 사용하는지는 좀 더 내부적으로 봐야 하는데 간단하게 설명하자면  
`Persistable` 을 구현하지 않은 엔티티의 경우는 기본 구현체인 `AbstractEntityInformation` 을 호출하게 되고   
구현한 경우에는 `JpaPersistableEntityInformation` 가 호출 되도록 `Spring Data JPA` 내부 로직이 작성되어 있다고 생각하면 된다.

```kotlin
public class JpaPersistableEntityInformation<T extends Persistable<ID>, ID>
		extends JpaMetamodelEntityInformation<T, ID> {

	/**
	 * Creates a new {@link JpaPersistableEntityInformation} for the given domain class and {@link Metamodel}.
	 * 
	 * @param domainClass must not be {@literal null}.
	 * @param metamodel must not be {@literal null}.
	 * @param persistenceUnitUtil must not be {@literal null}.
	 */
	public JpaPersistableEntityInformation(Class<T> domainClass, Metamodel metamodel,
			PersistenceUnitUtil persistenceUnitUtil) {
		super(domainClass, metamodel, persistenceUnitUtil);
	}

	@Override
	public boolean isNew(T entity) {
		return entity.isNew();
	}

	@Nullable
	@Override
	public ID getId(T entity) {
		return entity.getId();
	}
}
```
여기서 `entity.isNew()` 를 호출하고 `return` 하는데 이게 바로 `Persistable` 의 `isNew()` 메서드다.  
우린 `Persistable` 을 `UserEntity` 에서 구현하고 있기 때문에 우리가 구현한 `isNew()` 메서드를 호출하여 사용하게 된다.

그럼 `UserEntity` 에서 구현한 `Persistable` 관련 메서드와 `markNotNew` 메서드에 대해 알아보자.

하나씩 설명 하자면
1. `isNew` : `true`, `false` 의 값을 저장하고 있는 프로퍼티
2. `isNew()` : `isNew` 프로퍼티의 값을 반환하는 메서드, 여기서 `true` 를 반환하면 `insert` 를 `false` 를 반환하면 `update` 가 동작하게 된다.
3. `getId()` : 현재 엔티티의 식별자(id) 를 반환하는 메서드
4. `markNotNew()` : 이게 정말 중요한 메서드인데, 이건 `isNew` 프로퍼티의 값을 설정해 주는 메서드로 `isNew` 가 항상 같은 값을 반환하게 되면 `insert` 랑 `update` 중 한가지 동작만 하게 되기 때문에 그걸 방지 하기 위한 메서드

동작을 흐름에 따라 살펴보자면
1. `UserEntity` 생성 -> `isNew : true`
2. `userRepository.save(enttiy)` 호출
3. `JpaPersistableEntityInformation.isNew(entity)` 호출
4. `isNew() → true → persist() (INSERT 수행)` -> `isNew : true`
5. `INSERT 직전에 @PrePersist → markNotNew() 호출` -> `isNew : false`
6. `이후 DB 조회 시 @PostLoad → markNotNew() 호출` -> `isNew : false`

4번 동작 이후 `isNew` 가 `false` 로 변경되기 때문에 그리고 이후 `DB` 에서 조회 시 `isNew` 가 `false` 로 변경 되기 때문에 최초에만 `insert` 가 발생하고 이후에는 `update` 가 발생하게 된다.

이렇게 구현하고 테스트 코트를 통해 직접 쿼리가 어떻게 발생되는지 살펴보자.

```kotlin
@DataJpaTest
class PersistableTest {
    @Autowired
    private lateinit var entityManager: TestEntityManager

    @Autowired
    private lateinit var userRepository: UserRepository
    
    @Test
    @DisplayName("Persistable 구현 했을때")
    fun persistableTest() {
        val stats: Statistics =
            entityManager.entityManager
                .unwrap(Session::class.java)
                .sessionFactory
                .statistics.also {
                    it.isStatisticsEnabled = true
                    it.clear()
                }

        // UserEntity() 를 생성해 줄 때 ID 값을 직접 설정해주고 있는 모습
        val entity = UserEntity(id = 1L, username = "test_user", password = "1234")
        userRepository.save(entity)
        userRepository.flush()

        val queryCount: Long = stats.prepareStatementCount
        println("Query Count: $queryCount")

        Assertions.assertThat(queryCount).isGreaterThanOrEqualTo(1)
    }
}
```
테스트 코드는 `Persistable` 을 구현하지 않았을때 작성한 코드와 `Assertions` 부분 만 제외하고 동일하다.

```text
Hibernate: 
    insert 
    into
        users
        (password, username, id) 
    values
        (?, ?, ?)
Query Count: 1
```
로그를 확인해 보면 `Persistable` 을 구현하지 않았을때 발생했던 `select` 가 사라진걸 볼 수 있다.

세번째 방법인 "`Persistable` 을 직접 구현" 을 활용하게 되면 조금은 복잡하지만 `Spring Data JPA` 의 기능을 모두 활용할 수 있으면서 불필요한 쿼리 발생을 줄일 수 있는게 된다.

3가지 방법들 중 정답은 없다. 상황이나 취향에 맞게 방법을 선택하고 활용하면 좋을것 같다.

아 참고로 "`UserEntity` 외에 다른 수 많은 `Entity` 가 있는데 이걸 모두 구현해서 사용해야 하나요?" 라는   
질문이 있을 수 있는데, `@MappedSuperclass` 를 사용하여 `BaseEntity` 를 만들고 그걸 상속 받는 형태로 구현하면 모든 `Entity` 에 직접 구현할 필요가 없어지게 된다.

간단하게 사이드 프로젝트에서 사용중인 `BaseEntity` 의 코드를 보면 아래와 같다.
```kotlin
@MappedSuperclass
internal abstract class BaseEntity() : Persistable<Long> {
    @Id
    val id: Long = SnowflakeIdCreator.nextId()

    @Column(nullable = false)
    val createdAt: Instant = Instant.now()

    @Column(nullable = false)
    var updatedAt: Instant = Instant.now()

    @Column(nullable = false)
    val createdBy: Long = 0L

    @Column(nullable = false)
    var updatedBy: Long = 0L

    @Transient
    private var isNew = true

    override fun isNew(): Boolean = isNew

    override fun getId(): Long? = id

    @PrePersist
    @PostLoad
    private fun markNotNew() {
        isNew = false
    }
}
```

---
## 💡 마무리
사실 이 글은 `Persistable` 의 구현 방법을 설명하는 글 이기도 하지만, 학습할때 사용했던 방식들이 아닌 다른 방식으로 `Spring Data JPA` 를 사용했을때 고려할 부분이 있다는 내용을 함께 알려주고 싶어 작성한 글이다.  
단순히 `Select` 쿼리 하나가 더 발생한게 뭐가 큰 문제냐고 할 수 있겠지만, 별거 아니라고 그냥 넘어가기 보다는   
왜 내 의도와 다른 동작을 하게 된건지 확인해보고 파악하는 습관이 갖는게 중요한것 같다.  
추가로 그 현상을 어떻게 하면 개선시킬 수 있을지도 함께 살펴보면 더더욱 좋을것 같다.

오랜만에 `Spring Data JPA` 내부 코드를 디버깅 모드로 하나씩 따라가보면서 살펴봤는데,  
예전이랑 달라진 코드들이 있는걸 알수 있었다. 정말 빠르게 변화하는 기술 특성상 모든걸 파악하고 있을순 없지만  
종종 내부 로직이 어떻게 되어 있는지 살펴보는 습관을 갖는것도 좋을것 같다.(일단 나부터)