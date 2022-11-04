---
title: (TEST)UnitTest
author: geombong
date: 2022-07-20 23:21:00 +0900
modified: 2022-07-20 23:21:00 +0900
categories: [TEST]
tags: [TEST]
pin: false
---

# UnitTest

> JUnit5, assertj-core 3.x 버전 기준

## Mockito

### @Mock

- `mock` 모의 객체 생성을 위한 어노테이션

### @InjectMocks

- 주입을 수행해야 하는 필드를 표시하기 위한 어노테이션

### @ExtendWith(MockitoExtension.class)

- `@ExtendWith`: `JUnit4`에서 사용되던 `@RunWith` 를 대체하는 어노테이션, 테스트 확장을 위한 `class` 선언에 사용된다.

- `MockitoExtension.class`: `@Mock` 어노테이션으로 모의 객체를 생성하기 위해 선언

	> [MockitoExtension.class](https://javadoc.io/doc/org.mockito/mockito-junit-jupiter/latest/org/mockito/junit/jupiter/MockitoExtension.html)

## BDDMockito

### 학습 내용

- `BDD(Behavior-Driven Development)` : 행위 주도 개발, 테스트 대상의 상태의 변화를 테스트 하는것이며 시나리오를 기반으로 테스트하는 패턴을 권장한다.
	- 권장하는 기본 패턴은 given-when-then 구조를 가진다.
	- Mockito 를 상속한 클래스(`public class BDDMockito extends Mockito`)

- `given`: 특정 상태에서 출발하여
- `when`: 어떤 상태 변화를 가했을 때
- `then`: 기대하는 상태로 완료되어야 한다.

```java
@Test
void given_when_then() throws Exception {
    //given
    Long articleId = 1L;
    ArticleComment expected = createArticleComment("content");
    given(articleCommentRepository.findByArticle_Id(articleId)).willReturn(List.of(expected));

    //when
    Page<ArticleCommentDto> actual = sut.searchArticleComment(articleId);

    //then
    assertThat(actual)
        .hasSize(1)
        .first()
        .hasFieldOrPropertyWithValue("content", expected.getContent());
    then(articleCommentRepository).should().findByArticle_Id(articleId);
}
```

- 게시글 Id로 게시글에 작성되어있는 댓글 리스트를 반환하는 간단한 테스트 예제

- `given`: `1L` 의 아이디를 가지는 `게시글`에 `댓글` 이 작성 되어 있는 상태를 만들고, `댓글 리포지토리`에서 해당 `게시글 아이디`를 가지고 댓글을 찾은 상태에서 출발

- `when`: `searchArticleComment()` 해당 메서드로 게시글 아이디에 해당하는 댓글을 찾았을때

- `then`: `content` 라는 내용을 가지는 댓글이 반환되어야 한다.

- `hasFieldOrPropertyWithValue` : 실제 개체가 지정된 값을 가진 지정된 필드 또는 속성을 가지고 있는지 확인(`content` 라는 값을 가진 `Object `가 있는지 확인)

	> [hasFieldOrPropertyWithValue Guide](https://www.javadoc.io/doc/org.assertj/assertj-core/latest/org/assertj/core/api/AbstractObjectAssert.html#hasFieldOrPropertyWithValue(java.lang.String,java.lang.Object))

- `then(articleCommentRepository).should().findByArticle_Id(articleId)` : `댓글 리포지토리`에서 `findByarticle_Id()` 라는 매서드가 동작 해야한다.

### 주의할 점

- Mockito Strict Stubbing and The UnnecessaryStubbingException

```java
@DisplayName("레이블 정보를 입력하면, 해당 레이블을 수정한다.")
@Test
void givenLabelInfo_whenUpdatingLabel_thenUpdatedLabel() throws Exception {
    //given
    Long labelId = 1L;
    String oldTitle = "labelTitle1";
    String updateTitle = "labelTitle2";
    Label label = createLabel(labelId, oldTitle);
    RequestLabelDto dto = createRequestLabelDto(updateTitle);
    given(labelRepository.findById(labelId)).willReturn(Optional.of(label));

    //when
    label.update(dto);

    //then
    assertThat(label.getTitle())
        .isNotEqualTo(oldTitle)
        .isEqualTo(updateTitle);

    then(labelRepository).should().findById(labelId);
}
```

- 에러 코드

```java
Wanted but not invoked:
labelRepository.findById(1L);
-> at
team20.issuetracker.service.LabelServiceTest.givenLabelInfo_whenUpdatingLabel_thenUpdatedLabel(LabelServiceTest.java:20)
Actually, there were zero interactions with this mock.
```

- 에러 문구

- 에러 원인 : Mockito 2.+ 새로 추가된 스터빙의 관한 이유로, 사용되지 않은 메서드가 `given`또는 `then`에 존재 하는 경우 발생한다. 
	업데이트 하는 로직이 `label` 안에 존재하긴 하나 `given` 에서 생성한 `label` 을 가지고 바로 `update` 를 실행하면서, `labelRepository` 를 거치지 않아 에러가 발생 하였다. 테스트 하는 로직이 시나리오에 맞지 않아 발생하거라 생각하면 조금 더 쉽게 원인을 알 수 있다.

	> [위에 에러에 관한 Bdeldung 글](https://www.baeldung.com/mockito-unnecessary-stubbing-exception)

```java
@DisplayName("레이블 정보를 입력하면, 해당 레이블을 수정한다.")
@Test
void givenLabelInfo_whenUpdatingLabel_thenUpdatedLabel() throws Exception {
    //given
    Long labelId = 1L;
    String oldTitle = "labelTitle1";
    String updateTitle = "labelTitle2";
    Label label = createLabel(labelId, oldTitle);
    RequestLabelDto dto = createRequestLabelDto(updateTitle);
    given(labelRepository.findById(labelId)).willReturn(Optional.of(label));

    //when
    labelRepository.findById(labelId).orElseThrow(() -> {
        throw new IllegalArgumentException("존재하지 않는 Label 입니다.");
    }).update(dto);

    //then
    assertThat(label.getTitle())
        .isNotEqualTo(oldTitle)
        .isEqualTo(updateTitle);

    then(labelRepository).should().findById(labelId);
}
```

- 수정한 코드 : `labelRepository` 에서 `labelId`에 해당하는 `Label` 을 찾아서 `Update` 로직을 수행하여, `findById()` 메서드를 사용하게 되서 
	에러가 해결되었다.

## REFERENCE

[Mockito Docs](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html)

[JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)

[AssertJ Docs](https://assertj.github.io/doc/)