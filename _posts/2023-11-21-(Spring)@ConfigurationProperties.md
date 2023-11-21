---
title: (Spring)@ConfigurationProperties
author: crispin
date: 2023-11-21 23:13:00 +0900
modified: 2023-11-21 23:13:00 +0900
categories: [Spring]
tags: [Spring]
pin: false
---

## Warning ‼️
```textile
- 아래 모든 내용은 제가 공부하며, 작성한 내용이므로 잘못된 내용이 포함될 수 있습니다.
- 잘못된 내용에 대해 댓글을 남겨주신다면 정말 감사드리겠습니다. 
```

## 글 작성 이유

스프링을 공부하면서, 유저가 회원가입을 했을때 메일을 통한 인증 관련 로직을 보던 중 예전에 토이 프로젝트를 진행했을때 사용했던 `@Value` 어노테이션을 사용하여 `yaml` 또는 `properties` 파일에서 환경 변수 값을 가져오는게 아닌 다른 방식이 있어 정리 하고자 글 작성

## @Value

우선 `@Value` 어노테이션에 대해 간략하게 알아보자.

### 간단한 예제

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
                       @Value("${jwt.expired-time-ms}") Long expiredTimeMs) {
        this.userEntityRepository = userEntityRepository;
        this.passwordEncoder = passwordEncoder;
        this.secretKey = secretKey;
        this.expiredTimeMs = expiredTimeMs;
    }
    ...
}
```
```yaml
jwt:
  secret-key: test-secret-key
  # 30 days
  expired-time-ms: 25223
```

- 예전에 토이 프로젝트를 할때 작성했던 `UserService` 와 `application.yml` 코드의 일부분이다.
- `jwt` 를 활용하여 유저 로그인 처리를 하고 있는 부분에서 `jwt` 의 `secret-key` 와 `jwt-expired-time` 을 `@Value` 어노테이션을 통해 외부에서 가지고와 활용을 하고 있다.
- `@Value` 어노테이션의 경우 필드, 메서드, 파라미터, 어노테이션에 붙여 사용이 가능하다.
- 위 코드에서는 파리미터에 붙여서 사용하고 있다.
- 추가적으로 스프링에서 제공하는 `SpEL` 도 사용이 가능하며, `SpEL` 사용 시 동적으로 값을 매핑해줄수 있다.

### 동작 원리

- `@Value` 를 사용한 곳에 값이 매핑 되는 시점은 `Bean` 이 생성되고 의존성이 주입되는 시점에 값이 매핑된다. 

### 장점

- 사용이 매우매우 편리하다. 별도의 설정 없이 `@Value` 어노테이션만 사용하여 값을 가져올 수 있다.

### 단점

- 구글에 검색해 보면 `@Value` 어노테이션을 활용하여, 값을 가져올때 값을 가져오지 못하고 `null` 값이 나온다는 내용이 매우 많다. 어느 시점에 값이 매핑되는지 정확하게 알고 있는것이 중요할것 같다.
- `application.yml` 파일에서 `key` 에 해당하는 값이 변경되는 경우 `@Value` 가 사용된 모든 곳에 값을 변경해야하는 번거로움이 있다.

## @ConfigurationProperties

- `@Value` 어노테이션 과 비슷하게 외부의 값을 가져올때 사용할 수 있다.
- 스프링 팀에서 권장하는 방법
```java
@ConfigurationProperties(prefix = "spring.jpa")
public class JpaProperties {
    ...
}

@ConfigurationProperties(prefix = "spring.data.redis")
public class RedisProperties {
    ...
}
```
- 위 코드에서 보이듯 `Jpa` 설정 값이나 `Redis` 설정 값 등등 우리가 `application.yml` 에서 설정해주는 외부 값을 `@ConfigurationProperties` 어노테이션을 사용해 가져오는걸 확인할 수 있다.

### 간단한 예제

- 이번에는 `JavaMailSender` 를 `Bean` 으로 등록 하고 사용할때 외부에서 값을 넣어줘야 하는 부분이 있어 사용하게 되었다.
```java
@ConfigurationProperties(prefix = "spring.mail")
public record MailSetting(String host, int port, String username, String password) {
}

@ConfigurationProperties(prefix = "spring.mail.properties.mail.smtp")
public record MailProperties(boolean auth, boolean starttls, int timeout) {
}

```
- 총 두개의 `record` 에서 `@ConfigurationProperties` 어노테이션을 통해 값을 가져와 사용하고 있다.
- 생성자 바인딩이 가능하여, `record` 와 사용했을때 매우 편리하게 사용이 가능하다.
- 만약 생성자가 여러개의 경우 `@ConstructorBinding` 어노테이션을 사용하여 바인딩할 생성자를 선택할 수 도 있다.
- 또 추가로 `@DefaultValue(value=defaultValue)` 어노테이션을 사용해 기본값을 넣어줄 수 도 있다.
- 다만 `@ConfigurationProperties` 을 사용할때 어노테이션을 활성화 시켜줘야하는 부분이 있어 이점에 유의해야한다.

```java
@SpringBootApplication
@ConfigurationPropertiesScan
public class MyApplication {

    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }

}
```
- 일반적으로 `Spring` 프로젝트를 생성했을때 만들어지는 main 메서드를 가지는 클래스 위에 `@ConfigurationPropertiesScan` 어노테이션을 붙여 사용가능하게끔 활성화 시킨다.
- `@ConfigurationPropertiesScan` 어노테이션을 사용할때 패키지 경로를 선언하여, 해당 패키지 경로에 있는 `@ConfigurationProperties` 어노테이션만 활성화 되도록 만들 수도 있다.

### 장점
- `Relaxed Binding` 사용이 가능하다.
    - Relaxed Binding: `application.yml` 과 바인딩 되는 값의 이름이 정확하게 일치하지 않더라도 바인딩을 해주는 방법
    - ex: PORT 와 port 는 대소문자로 차이가 있지만 `@ConfigurationProperties` 어노테이션을 사용하면 바인딩이 가능하다.
    - 위 예제 외에 몇가지 완화된 규칙을 가지고 바인딩을 해주기 때문에 편리하게 사용이 가능하며, 자세한 내용은 아래 공식 문서에서 확인이 가능하다.
- 메타데이터를 지원한다.

### 단점
- `SpEL` 의 사용이 불가능하다.(단점 맞나??)
- 처음 사용할때 초기 설정이 필요하다.
    - 활성화와 바인딩을 위한 객체 생성 등

## @Value 와 @ConfigurationProperties 차이

### 차이표

|특징|@ConfigurationProperties|@Value|
|----|-----|----|
|[Relaxed binding](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.external-config.typesafe-configuration-properties.relaxed-binding)|O|부분적 지원|
|[Meta-data support](https://docs.spring.io/spring-boot/docs/current/reference/html/configuration-metadata.html#appendix.configuration-metadata)|O|X|
|`SpEL` evaluation|X|O|

### 선택 기준
- 공식 문서에서는 `@ConfigurationProperties` 어노테이션을 사용한 POJO 를 통해 그룹화 하는것을 권장하고 있으며, 만약 `SpEL` 을 사용하여 값을 처리해야 경우에 `@Value` 를 사용하면 좋다고 한다.

----

## REFERENCE

- [SpringApplication Docs](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.external-config.typesafe-configuration-properties)
