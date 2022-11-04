---
title: (TEST)테스트 중 @Value Null 문제
author: geombong
date: 2022-10-27 15:06:00 +0900
modified: 2022-10-27 15:06:00 +0900
categories: [TEST]
tags: [TEST]
pin: false
---



# 테스트 중 @Value Null 문제

## 문제 상황
- `JWT` 를 활용하는 프로젝트를 진행하는 도중에 외부에 노출되어서는 안되는 값을 `local.yml` 파일에 등록하여 관리하고 있었는데
  단위 테스트를 진행하면서, `@Value` 를 통해 `local.yml` 파일에 명시 해둔 값을 가져오는 과정에서 값을 가져오지 못하고 `null` 값으로 처리되는 문제가 발생

  

![@value null2](https://user-images.githubusercontent.com/78953393/198202967-854b5c38-8892-43d1-87a4-33213cc50d67.png)
- 디버깅 창에서 보이듯이 값이 `null` 로 설정되어 있다.



## 문제 코드

### local.yml

```yml
jwt:
  secret-key: secrty-key-example
  # 30 days
  expired-tine-ms: 2592000000
```
- `JWT` 를 생성할때 필요하면서, 외부에 노출되어서는 안되는 값을 `local.yml` 파일에 등록하여 관리하는 중, 배포할때는 환경변수를 사용해야 하기 때문에 `${JWT_SECRET_KEY}` 와 `${JWT_EXPORED_TIME_MS}` 로 바꿔 배포할 예정이다.



### UserService.java

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserEntityRepository userEntityRepository;
    private final BCryptPasswordEncoder passwordEncoder;

    @Value("${jwt.secret-key}")
    private String secretKey;

    @Value("${jwt.expired-tine-ms}")
    private Long expiredTimeMs;
    
    public String login(String username, String password) {

        UserEntity userEntity = userEntityRepository.findByUsername(username).orElseThrow(
                () -> new SnsApplicationException(ErrorCode.USER_NOT_FOUND, String.format("%s not founded", username))
        );

        if (!isPasswordValid(password, userEntity)) {
            throw new SnsApplicationException(ErrorCode.INVALID_PASSWORD);
        }

        return JwtTokenUtils.generateToken(username, secretKey, expiredTimeMs);
    }

    private boolean isPasswordValid(String password, UserEntity userEntity) {
        return passwordEncoder.matches(password, userEntity.getPassword());
    }
}
```
- 문제의 `@Value` 를 사용하는 `Service` 코드
- 유저가 로그인을 시도하고, 로그인에 성공하였을 경우 `JWT` 토큰을 생성하여 `Controller` 로 반환해주는 로직이 있다.
- 여기서 `JwtTokenUtils` 사용해서 `JWT` 토큰을 생성하여 반환해 주고 있는데, 이곳에서 `local.yml` 에 등록되어 있는 값이 필요하다.



### UserServiceTest.java

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @InjectMocks
    private UserService userService;

    @Mock
    private UserEntityRepository userEntityRepository;

    @Mock
    private BCryptPasswordEncoder passwordEncoder;
    
    @Test
    void loginSuccessTest() {
        String username = "username";
        String password = "password";
        UserEntity userEntity = UserEntityFixture.get(username, password);

        given(userEntityRepository.findByUsername(username)).willReturn(Optional.of(userEntity));
        given(passwordEncoder.matches(password, userEntity.getPassword())).willReturn(true);

        Assertions.assertThatCode(() ->
                        userService.login(username, password))
                .doesNotThrowAnyException();

        then(userEntityRepository).should().findByUsername(username);
        then(passwordEncoder).should().matches(password, userEntity.getPassword());
    }
}
```
- `UserService` 로직 중에 `login` 성공 상황을 테스트하는 코드
- 다른것은 `mocking` 을 통해 해결이 되었는데, `login()` 메서드 마지막에 `JWT` 를 반환해주는 곳에서 문제가 발생했다.
- 위에 말하였듯이 `@SpringBootTest` 어노테이션을 사용하지 않고, `Unit` 테스트를 진행하고 있었는데 여기서 `@Value` 의 값을 넣어줘야 하는데 `Spring` 없이 테스트를 하고 있어서 값을 넣어주지 못하고 있었다.
- 코드를 실행하면 `NPE` 가 발생하는 상황💧



## 문제 해결 방법

1. `@SpringBootTest` 어노테이션을 사용한다.(가장 빠르고 쉬운 해결 방법)
2. `ReflectionTestUtils` 를 사용해여 필드값을 셋팅해준다.(Reflection.. 최후의 수단)
3. `@Value` 를 필드가 아닌 `생성자`의 매개변수에 선언하고, 테스트에서 `Service` 를 생성해서 사용하는 방법



### @SpringBootTest

```yml
spring:
  profiles:
    default: test
```
- `application.yml` 에 `default profiles` 를 `test` 로 지정

    

```yml
jwt:
  secret-key: test-secret-key
  # 30 days
  expired-tine-ms: 25223
```
- `application-test.yml` 에 테스트 용도로 사용할 값을 설정

    

```java
@SpringBootTest
class UserServiceTest {

    @Autowird
    private UserService userService;
    ...
}
```
- `@SpringBootTest` 어노테이션을 사용하고, `UserService` 를 `@Autowird` 해준다.

- 이 방법은 매우 쉽지만, `Unit 테스트`를 하고자 했던 테스트 방식을 통합 테스트 방식으로 변경해야 하는 치명적인 단점이 있다.

    

### ReflectionTestUtiles
```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @InjectMocks
    private UserService userService;

    @Mock
    private UserEntityRepository userEntityRepository;

    @Mock
    private BCryptPasswordEncoder passwordEncoder;

    @BeforeEach
    public void setUp() {
        ReflectionTestUtils.setField(userService, "secretKey", "test-secret-key");
        ReflectionTestUtils.setField(userService, "expiredTimeMs", 25223L);
    }
}
```
- 다른 별도의 설정 없이 `Unit 테스트`를 하고 있던 코드에 `@BeforeEach` 를 사용하여 `Test` 를 `setUp` 해주는 메서드에 `ReflectionTestUtils.setField()`` 를 활용해, 필드 값을 강제로 설정해주는 방식을 사용 할 수 있다.

- `Unit 테스트`를 유지하면서, 정말 간단하게 `@Value` 를 사용하던 필드에 값을 넣어 줄 수 있다.

- `Reflection` 을 사용하긴 하지만, 그래도 `Test` 용도로만 사용하는 것이니 크게 문제될것 없을것이라 생각했다. 

- `Reflection` 을 통한 `set` 방식을 무분별하게 사용하면 변경에 너무 열려있는 코드가 되는것 같아 혹시 또 다른 방법은 없을지 찾아 보기로 했다.

    

```java
14:32:23.988 [main] DEBUG org.springframework.test.util.ReflectionTestUtils - Setting field 'secretKey' of type [null] on target object [com.bong.sns.service.UserService@3003697] or target class [class com.bong.sns.service.UserService] to value [test-secret-key]

14:32:23.990 [main] DEBUG org.springframework.test.util.ReflectionTestUtils - Setting field 'expiredTimeMs' of type [null] on target object [com.bong.sns.service.UserService@3003697] or target class [class com.bong.sns.service.UserService] to value [25223]
```
- 추가적으로 `Reflection` 방식을 사용하면 `Spring` 콘솔에 해당 로그가 찍힌다.

    

![Replcation debug](https://user-images.githubusercontent.com/78953393/198202980-2797b00e-8369-4c43-941f-820332a71956.png)
- `null` 값으로 설정되던 필드들이 `ReflectionTestUtils` 통해 `set` 해준 값으로 설정된걸 확인할 수 있다. 



### 테스트에서 Service 를 생성하여 사용

```java
@Service
@Transactional(readOnly = true)
public class UserService {

    private final UserEntityRepository userEntityRepository;
    private final BCryptPasswordEncoder passwordEncoder;

    private String secretKey;

    private Long expiredTimeMs;

    public UserService(UserEntityRepository userEntityRepository,
                       BCryptPasswordEncoder passwordEncoder,
                       @Value("${jwt.secret-key}") String secretKey,
                       @Value("${jwt.expired-tine-ms}") Long expiredTimeMs) {
        this.userEntityRepository = userEntityRepository;
        this.passwordEncoder = passwordEncoder;
        this.secretKey = secretKey;
        this.expiredTimeMs = expiredTimeMs;
    }
    
    public String login(String username, String password) {

        UserEntity userEntity = userEntityRepository.findByUsername(username).orElseThrow(
                () -> new SnsApplicationException(ErrorCode.USER_NOT_FOUND, String.format("%s not founded", username))
        );

        if (!isPasswordValid(password, userEntity)) {
            throw new SnsApplicationException(ErrorCode.INVALID_PASSWORD);
        }

        return JwtTokenUtils.generateToken(username, secretKey, expiredTimeMs);
    }
}
```
- `Service` 에서 `@Value` 의 값을 가져오도록 필드값에 지정하는 것이 아니라, 생성자의 매개변수에 지정

    

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @InjectMocks
    private UserService userService;
    
    @Test
    void loginSuccessTest() {
        String username = "username";
        String password = "password";
        
        // test 용 Jwt 설정 값
        String secretKey = "test-secret-key";
        Long expiredTimeMs = 25223L;
        UserEntity userEntity = UserEntityFixture.get(username, password);
        
        // 새로운 UserService 를 생성하면서, 생성에 필요한 인자 값을 넣어준다.
        UserService newUserService = new UserService(userEntityRepository, passwordEncoder, secretKey, expiredTimeMs);

        given(userEntityRepository.findByUsername(username)).willReturn(Optional.of(userEntity));
        given(passwordEncoder.matches(password, userEntity.getPassword())).willReturn(true);

        Assertions.assertThatCode(() ->
                        newUserService.login(username, password))
                .doesNotThrowAnyException();

        then(userEntityRepository).should().findByUsername(username);
        then(passwordEncoder).should().matches(password, userEntity.getPassword());
    }
}
```
- 테스트 용도로 사용할 `UserService` 를 생성하고, 생성할때 `JWT` 설정 값과 필요한 값을 인자 값으로 넣어준다.

- 생성된 `UserService` 를 테스트에서 사용하기 때문에 @Value 를 통해 값을 가져오지 않더라도, 해당 필드값에는 `null` 이 아닌 우리가 넘겨준 값이 설정되게 된다.

- 코드에 변경이 위에 방법에 비해 다소 많지만, 생성자를 통한 주입으로 `field` 주입과 `setter` 주입이 좋지 않아 사용하면 안된다는 문제도 함께 해결이 가능하다. (@Value 를 필드에 선언하는 것도 하나의 필드 주입이라 생각한다.)

- `Unit 테스트`도 유지 할 수 있고, `Reflection` 을 사용하지도 않으며, `Debug 로그`가 찍히지도 않는다. 앞으로 `@Value` 가 있는 경우 테스트를 진행해야 한다면 위에 방식을 사용하지 않을까 싶다.

    

![생성자 주입 디버그](https://user-images.githubusercontent.com/78953393/198202973-b4cd7e36-1190-4087-9cea-c910728a8767.png)
- 당연하지만, 값이 잘 설정되어 있는걸 확인할 수 있다.



### 그 외

- 구글에 검색해보면 위에 명시한 방법 외에도 다양한 해결방법이 있는것 같다. 상황에 따라 위에 상황을 활용하지 못하게 된다면 또 다른 방법을 적용해 보면 좋을것 같다.



## @Value

- 사용하면서 조금 불편했던 것이 `key` 의 값이 변경될 경우 `@Value` 를 사용한 모든 곳을 일일이 찾아서 `key` 값을 변경해 줘야 하는 불편함이 있었다.
- 찾아보니 `@Value` 를 사용하는것이 좋지 못한 방법이라는 이야기도 있다. 우선 이 글에서는 `@Value` 를 사용한 상태에서 테스트 작성을 위주로 하기 때문에 다음에 `@Value` 를 대체할 방법에 대해 포스팅 해봐야겠다.