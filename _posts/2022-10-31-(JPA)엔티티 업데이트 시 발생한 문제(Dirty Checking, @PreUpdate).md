---
title: (JPA)엔티티 업데이트 시 발생한 문제(Dirty Checking, @PreUpdate)
date: 2022-10-31 18:18:00 +0900
modified: 2022-10-31 18:18:00 +0900
categories: [JPA]
tags: [JPA]
pin: false
---

# 엔티티 업데이트 시 발생한 문제(Dirty Checking, @PreUpdate)
- ~~제목을 딱 짧고 명확하게 하기 어려워 주저리 주저리 썼다.~~



## 문제 상황

- 글을 작성하고, 수정할 수 있는 간단한 프로젝트를 하던 와중에 `글(Post)` 을 수정할때 수정 시간을 `@PreUpdate` 를 통해 값을 넣어주고 있었는데 여기서 `문제`가 발생하였다.
- `엔티티`를 수정하고, 수정된 `엔티티`를 반환받아 `Json` 으로 뿌려주고 있었는데 분명 `DB` 에는 수정 시간이 잘 등록되고 있는데 `반환받은 값` 에는 `수정 시간 값` 이 제대로 등록되어 있지 않은 문제 발생
- 조금만 생각해 보면 왜 그런지 쉽게 풀 수 있는 문제 였으나, 그래도 이왕 이런 문제가 발생하였으니 `영속성 관리` 와 `엔티티 수정` 시 주의할 점을 함께 작성해 보면 좋을것 같아 글을 쓰게 되었다.



### Update query

```sql
update
    "post" 
set
    body=?,
    deleted_at=?,
    registered_at=?,
    title=?,
    updated_at=?,
    user_id=? 
where
    id=?
```
- `Dirty Checking` 을 통해 `Update query` 가 발생하고 있다.



### DB 상태

![DB 상태](https://user-images.githubusercontent.com/78953393/198972246-a51b46fd-ae7f-4d36-b241-d8a15526d40d.png)
- `DB` 값을 보면 분명 업데이트가 정상적으로 이뤄지고, 업데이트 시간 또한 값을 잘 들어와 있는걸 볼 수 있다.



### Json 반환

```json
{
    "resultCode": "SUCCESS",
    "result": {
        "id": 2,
        "title": "updated title",
        "body": "updated body",
        "user": {
            "id": 1,
            "username": "test1",
            "role": "USER",
            "registeredAt": "2022-10-30T15:53:31.049+00:00",
            "updatedAt": null,
            "deletedAt": null
        },
        "registeredAt": "2022-10-31T07:44:21.642+00:00",
        "updatedAt": null,
        "deletedAt": null
    }
}
```
- 위에 `DB` 값처럼 `title` 과 `body` 의 값은 잘 변경되어 뿌려지는걸 볼 수 있으나, `updatedAt` 의 값은 `null` 로 반환되고 있는걸 볼 수 있다.



## 문제 코드

### PostService

```java
@Service
public class PostService {
    ...
    
    @Transactional
    public Post modify(Long postId, String title, String body, String username) {
        ...
        PostEntity modifyPostEntity = postEntity.updatePost(title, body);
        return Post.from(modifyPostEntity);
    }
}
```
- `글(Post)` 을 수정하는 로직이 있는 `PostService class` 에 `modify()` 메서드 코드이다.
- 수정값을 매개변수로 받아서, `PostEntity` 의 `updatePost()` 메서드로 인자값을 보내 `PostEntity` 내부에서 값을 변경하는 로직이다.
- 내부의 값이 변경되면서, 트랙젝션이 종료될때 `Dirty Checking` 을 통해 `DB` 에 업데이트가 이뤄지고 있다.



### PostEntity

```java
@Entity
public class PostEntity {
    ...
    
    private Timestamp updatedAt;
    
    @PreUpdate
    void updatedAt() {
        this.updatedAt = Timestamp.from(Instant.now());
    }
    
    public PostEntity updatePost(String title, String body) {
            this.title = title;
            this.body = body;
            return this;
    }
    
    ...
}
```
- `PostEntity` 내부의 `updatePost()` 메서드
- 매개변수로 `title` 과 `body` 값을 받아서, 값을 변경 하고 자기자신을 `return` 해주고 있다. 



### PostController

```java
@RestController
@RequestMapping("/api/v1/posts")
@RequiredArgsConstructor
public class PostController {
    ...
    
    @PutMapping("/{postId}")
    public Response<PostResponse> modify(
        @RequestBody PostModifyRequest request,
        @PathVariable Long postId
    ) {
        Post modifyPost = postService.modify(postId, request.getTitle(), request.getBody());
        return Response.success(PostResponse.from(modifyPost));
    }
}
```
- 업데이트에 필요한 `PostService` 내부의 `modify()` 를 호출해주고 있으며, `modify()` 메서드에서 반환된 값을 `PostResponse` 로 변환하여 클라이언트 쪽으로 보내주고 있다.



## 문제 원인

### 첫번째 원인

- `@PreUpdate` 는 과연 언제 `updatedAt` 에 값을 넣어주고 있는가?

    

```java
@Entity
public class PostEntity {
    ...
    
    private Timestamp updatedAt;
    
    @PreUpdate
    void updatedAt() {
        this.updatedAt = Timestamp.from(Instant.now());
    }
    
    public PostEntity updatePost(String title, String body) {
            this.title = title;
            this.body = body;
            return this;
    }
    
    ...
}
```
- `PostEntity` 에서 사용중인 `@PreUpdate` 는 현재 상황에서는 `트랙젝션 커밋` 되기전, `flush()` 가 발생한 이후 `Dirty Checking` 이 일어나 `Update Query` 가 발생하며 그 순간 `UpdatedAt` 에 값이 들어가게 된다.



### 두번째 원인

- 영속성 관리에서 `flush()` 는 언제 발생하는가?

    

```java
@Service
public class PostService {
    ...
    
    @Transactional
    public Post modify(Long postId, String title, String body, String username) {
        ...
        PostEntity modifyPostEntity = postEntity.updatePost(title, body);
        return Post.from(modifyPostEntity);
    }
}
```
- `@Transactional` 어노테이션을 달려 있는 메서드의 활동이 종료되는 순간 `트랜젝션 커밋` 이 발생하게 되면 `커밋하기 전` 에 엔티티 매니저 내부에서 `flush()` 가 먼저 호출된다.



### 세번째 원인

- 업데이트 직후 그 값을 받아 바로 뿌려주는건 좋게 `설계` 되어 있는 동작인가?

    

```java
@RestController
@RequestMapping("/api/v1/posts")
@RequiredArgsConstructor
public class PostController {
    ...
    
    @PutMapping("/{postId}")
    public Response<PostResponse> modify(
        @RequestBody PostModifyRequest request,
        @PathVariable Long postId
    ) {
        Post modifyPost = postService.modify(postId, request.getTitle(), request.getBody());
        return Response.success(PostResponse.from(modifyPost));
    }
}
```
- 위 처럼 값을 수정하고, 바로 반환된 값을 클라이언트에 보내준다면 아무래도 조회를 다시 하는 번거로움을 사라질것 같긴 하지만 `"조회와 로직은 따로 분리하는게 더 좋은 설계다."` 라고 영한님께서 말씀하신적이 있어 좀 더 고민해 봐야하는 문제인것 같다.



## 문제 해결

### 첫번째 방법

- 조회와 업데이트 로직을 `분리` 한다.

    

```java
@Service
public class PostService {
    ...
    
    @Transactional
    public void modify(Long postId, String title, String body, String username) {
        ...
        PostEntity modifyPostEntity = postEntity.updatePost(title, body);
    }
}


    @RestController
    @RequestMapping("/api/v1/posts")
    @RequiredArgsConstructor
    public class PostController {
    ...
    
    @PutMapping("/{postId}")
    public Response<Void> modify(
        @RequestBody PostModifyRequest request,
        @PathVariable Long postId
    ) {
        Post modifyPost = postService.modify(postId, request.getTitle(), request.getBody());
        return Response.success();
    }
}
```
- `PostService` 와 `PostController` 에서 업데이트 이후의 값을 반환받아 클라이언트로 보내는 것이 아니라 업데이트는 업데이트만 진행을 하고 조회는 따로 조회만을 진행하는 방향으로 설계를 바꾸는 것이다.



### 두번째 방법

- `EntityManager` 를 통해 `flush()` 를 발생시켜준다.

    

```java
@Service
@RequiredArgsConstructor
public class PostService {
    ...
    
    @PersistenceContext
    private final EntityManager entityManager;
    
    @Transactional
    public Post modify(Long postId, String title, String body, String username) {
        ...
        PostEntity modifyPostEntity = postEntity.updatePost(title, body);
        entityManager.flush();
        return Post.from(modifyPostEntity);
    }
}
```
- 직접 `EntityManager` 를 주입 받아서 `updatePost()` 메서드가 종료되는 시점 이후 `flush()` 해주게 되면 현재 변경되어 있는 값이 즉시 적용되어 `updatedAt` 의 값도 의도한대로 잘 들어가게 된다.

    

![flush DB 값](https://user-images.githubusercontent.com/78953393/198972257-bae3550a-e7a3-41f0-859f-2a7b49e0ec47.png)
- `DB` 상태 또한 잘 변경되는걸 볼 수 있다.

    

```json
{
    "resultCode": "SUCCESS",
    "result": {
        "id": 2,
        "title": "updated title!",
        "body": "updated body!",
        "user": {
            "id": 1,
            "username": "test1",
            "role": "USER",
            "registeredAt": "2022-10-30T15:53:31.049+00:00",
            "updatedAt": null,
            "deletedAt": null
        },
        "registeredAt": "2022-10-31T07:44:21.642+00:00",
        "updatedAt": "2022-10-31T08:42:20.460+00:00",
        "deletedAt": null
    }
}
```
- `Json` 반환 또한 `updatedAt` 의 값이 잘 들어가 있는걸 볼 수 있다.
- `08:42 + 9` 를 하게되면 한국 시간으로 되어 `17시 42분` 에 `update` 된걸 알 수 있다.



### 세번째 방법

- `JPA` 에서 제공해주고 있는 `save()` 대신 `saveAndFlush()` 를 사용한다.

- `Dirty Checking` 을 통해 업데이트를 진행하는 것이 아니라 `postEntityRepository` 에서 `saveAndFlush()` 를 사용해서 `update` 와 동시에 `flush()` 를 시켜주면 된다.

    

```java
@Service
@RequiredArgsConstructor
public class PostService {
    ...
    
    private final PostEntityRepository postEntityRepository;
    
    @Transactional
    public Post modify(Long postId, String title, String body, String username) {
        ...
        
        PostEntity modifyPostEntity = postEntityRepository.saveAndFlush(
                postEntity.updatePost(title, body)
        );
        return Post.from(modifyPostEntity);
    }
}
```
- `postEntityRepository.saveAndFlush()` 를 사용하게 되면 `save` 와 동시에 `flush()` 가 발생하여, 변경사항을 즉시 적용하게 된다.

    

```java
@Repository
@Transactional(readOnly = true)
public class SimpleJpaRepository<T, ID> implements JpaRepositoryImplementation<T, ID> {
    ...

    @Transactional
    @Override
    public <S extends T> S saveAndFlush(S entity) {

        S result = save(entity);
        flush();

        return result;
    }

    @Transactional
    @Override
    public <S extends T> S save(S entity) {

        Assert.notNull(entity, "Entity must not be null.");

        if (entityInformation.isNew(entity)) {
            em.persist(entity);
            return entity;
        } else {
            return em.merge(entity);
        }
    }

    @Transactional
    @Override
    public void flush() {
        em.flush();
    }

    ...
}
```
- `save()` 메서드의 경우 `isNew` 즉 새로운 `entity` 가 아니면 `merge` 를 새로운 `entity` 이면 `persist` 해주고 있는걸 볼 수 있다.

- 즉 이 방법은 `변경감지에 의한 업데이트` 가 아니라 `병합을 통한 업데이트` 가 이뤄지고 있는걸 알 수 있다.

- `saveAndFlush()` 의 메서드 경우 확인해 보면 두번째 방법에서 처럼 `EntityManager` 를 통해 `flush()` 를 해주고 있는걸 볼 수 있다.

    

![saveAndFlush](https://user-images.githubusercontent.com/78953393/198972263-a58821f5-bf63-4b0b-aa2c-06e189ec66fe.png)
- `DB` 상태 또한 잘 변경되는걸 볼 수 있다.

    

```json
{
    "resultCode": "SUCCESS",
    "result": {
        "id": 2,
        "title": "updated title!!!!",
        "body": "updated body!!!!",
        "user": {
            "id": 1,
            "username": "test1",
            "role": "USER",
            "registeredAt": "2022-10-30T15:53:31.049+00:00",
            "updatedAt": null,
            "deletedAt": null
        },
        "registeredAt": "2022-10-31T07:44:21.642+00:00",
        "updatedAt": "2022-10-31T08:52:00.616+00:00",
        "deletedAt": null
    }
}
```
- `Json` 반환 또한 `updatedAt` 의 값이 잘 들어가 있는걸 볼 수 있다.

- `08:52 + 9` 를 하게되면 한국 시간으로 되어 `17시 52분` 에 `update` 된걸 알 수 있다.

    

## 정리

### 앞으로

- 앞으로는 `설계를 분리`해서 이런 문제가 발생할 여지조차 주지 않는 방향으로 작업을 진행할 것 같지만, 그게 안되는 상황에서는 `두번째 방법`을 사용하지 않을까 싶다. 아무래도 `병합`을 통한 업데이트는 영한님께서도 주의를 해야한다고 강의에서 말씀하신 적이 있는것 같아서 사용하는데 있어 조심스러울것 같다.



### 느낌점

- 알고있다고 생각하는게 가장 무서운 거라고, 분명 코드를 작성할때는 문제가 없을것이라 생각했지만 아니였다. 좀 만 생각해보면 풀 수 있는 문제 였지만 그래도 처음부터 문제가 없는게 제일 좋은것이니 앞으로는 `Entity` 의 업데이트 로직을 작성할때는 좀 더 주의를 해야할 것 같다.

    

---

## REFERENCE

[자바 ORM 표준 JPA 프로그래밍 - 기본편](https://www.inflearn.com/course/ORM-JPA-Basic)

