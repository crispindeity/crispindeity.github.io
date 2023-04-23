---
title: (Project)API 최적화
author: geombong
date: 2022-10-09 23:30:00 +0900
modified: 2022-10-09 23:30:00 +0900
categories: [Project]
tags: [Project]
pin: false
---

# API 최적화(N+1)

## 모든 Issue 조회 API
- `모든 Issue 조회 시` 하나의 Issue마다 `8개`의 SELECT QUERY가 발생
    - 하나의 Issue에 Milestone, Label, Comment, Assignee가 각 1개 있는 기준
    - 각기 다른 Label, Milestone, Comment, Assignee가 있을 경우 더 많은 Query가 발생될 것으로 예상
- Issue의 개수에 따라 지연로딩으로 인한 여러번의 반복 쿼리가 발생
    - 1차 캐쉬에 데이터가 없는 기준으로 8개의 쿼리가 발생하고 있는데, 위의 경우 처럼 각기 다른 종류의 Label 등을 하나씩만 가지고 있는 Issue가 
        100개 라면 801개의 조회 쿼리가 발생하게 된다.

## 문제 발생

### 문제 발생 구간
- 모든 Issue를 조회하고, DTO로 반환하는 곳에서 지연로딩으로 프록시로 되어있던 데이터들이 엔티티 데이터로 변환되는 과정에서 문제 발생

    

```java
private List<ResponseIssueDto> responseIssueDtos(List<Issue> findIssues) {
    return findIssues.stream()
            .map(ResponseIssueDto::of)
            .collect(Collectors.toList());
}
```
- 스트림을 활용해 조회해온 Issue를 DTO로 변환하는 메서드

- 이부분에서 Issue의 개수 많큼 DTO를 로 변환하는 of 메서드를 호출

    

```java
public static ResponseIssueDto of(Issue issue) {
    List<ResponseMilestoneDto> milestones = new ArrayList<>();

    if (issue.getMilestone() != null) {
        milestones = List.of(ResponseMilestoneDto.from(issue.getMilestone()));
    }

    return new ResponseIssueDto(
            issue.getId(),
            issue.getTitle(),
            issue.getMember().getName(),
            issue.getMember().getProfileImageUrl(),
            issue.getComments().size(),
            issue.getContent(),
            issue.getCreatedAt(),
            issue.getStatus().toString().toLowerCase(),
            milestones,
            issue.getComments().stream()
                    .map(ResponseCommentDto::from)
                    .collect(Collectors.toList()),
            issue.getIssueLabels().stream()
                    .map(IssueLabel::getLabel)
                    .map(ResponseLabelDto::from)
                    .collect(Collectors.toList()),
            issue.getIssueAssignees().stream()
                    .map(IssueAssignee::getAssignee)
                    .map(ResponseAssigneeDto::from)
                    .collect(Collectors.toList()));
}
```
- DTO를 생성 하는 메서드
- 위 메서드에서 지연로딩으로 인해 프록시 객체로 되어있는 객체를 엔티티 객체로 변환된다.
- 프록시 객체로 되어있는 객체를 엔티티 객체로 변환하는 과정에서 SELECT QUERY가 발생

## 해결 방법

- `N + 1` 의 대표적인 해결 방법인 `FETCH JOIN` 과 `BATCH_FETCH_SIZE` 를 설정하여 해결
- 모든 Issue 조회 시 모든 연관관계 엔티티에 FETCH JOIN을 사용하고 DISTINCT로 중복된 데이터를 제거하는 방법으로 N+1 문제를 해결 할 수도 있으나, 이 경우 OneToMany 관계의 엔티티도 FETCH JOIN을 하게 되어 페이징 관련 SQL이 발생하지 않고, 메모리에서 페이징 처리를 진행하게 되면서 Memory out bound exception 예외가 발생 할 수 있어 해당 방법을 사용하지 않았다.
    - OneToMany에서 JOIN을 할 경우 Many의 수 많큼 데이터가 늘어나면서 DB 자체에서 페이징을 할수가 없게된다.
    - Hibernate 경고 로그 발생
    - 추가적으로 OneToMany 컬렉션 FETCH JOIN은 1개만 사용할 수 있다. 여러개를 사용할 경우 데이터가 부정확하게 조회될 수 있다.

### FETCH JOIN

- Issue 엔티티에서 XToOne 관계를 가지고 있는 엔티티에 대해 FETCH JOIN을 사용해서 지연로딩을 강제 초기화 시킨다.

- XToOne 관계는 JOIN으로 인한 데이터의 증가가 없기 때문에 FETCH JOIN을 사용

    

```java
@Query("select i from Issue i join fetch i.member m join fetch i.milestone mi")
List<Issue> findAllIssue();
```
- XToOne 관계를 가지는 member, milestone 엔티티에 fetch join 사용

### BATCH_FETCH_SIZE
- XToMany 관계의 엔티티에 대해 페이징 문제와 프록시 문제를 해결하기 위해 사용

- BATCH_FETCH_SIZE 를 설정하면 IN Query 를 사용해서 Issue 관련된 Label, Comment, Assignee 를 각각 하나의 쿼리로 SIZE 만큼의 데이터를 가져온다.

- SIZE 만큼의 데이터를 미리 다 가져오기 때문에 지연로딩으로 인해 발생되는 SELECT QUERY를 줄일 수 있다.

    

```sql
select
    label0_.id as id1_5_0_,
    label0_.author_id as author_i2_5_0_,
    label0_.created_at as created_3_5_0_,
    label0_.updated_at as updated_4_5_0_,
    label0_.background_color as backgrou5_5_0_,
    label0_.description as descript6_5_0_,
    label0_.text_color as text_col7_5_0_,
    label0_.title as title8_5_0_ 
from
    label label0_ 
where
    label0_.id=?
```
- BATCH_FETCH_SIZE 설정 하기 전 쿼리

- Label 데이터를 각각 하나씩 가져오게 된다.
    - Label 의 개수 만큼 SELET QUERY 발생
    
        

```sql
select
    label0_.id as id1_5_0_,
    label0_.author_id as author_i2_5_0_,
    label0_.created_at as created_3_5_0_,
    label0_.updated_at as updated_4_5_0_,
    label0_.background_color as backgrou5_5_0_,
    label0_.description as descript6_5_0_,
    label0_.text_color as text_col7_5_0_,
    label0_.title as title8_5_0_ 
from
    label label0_ 
where
    label0_.id in (
        ?, ?
    )
```
- BATCH_FETCH_SIZE 설정 하기 후 쿼리
- Label 데이터가 IN QUERY로 설정한 SIZE 만큼의 데이터를 한번에 가져온다.

## 성능 개선
### 발생 QUERY 개수
- Issue 하나 당 8개의 QUERY가 발생하던 상황에서 여러개의 Issue가 있어도 6개의 QUERY 만으로 조회가 가능하도록 변경되었다.

    

### 조회 속도

```
- Issue: 500개
- Lebel: 7개
- Milestone: 2개
- Comment: 100개
```
- 랜덤 더미 데이터 개수
- 개선 전: 모든 이슈 조회 시 약 1500개의 SELETE QUERY가 발생하면서, 많은 데이터의 양이 아님에도 조회에 10초 이상의 시간 소요
- 개선 후: BATCH_FETCH_SIZE 500 기준 단 6개의 SELETE QUERY로 조회 완료, 시간 또한 조회 버튼을 클릭하자마자 바로 결과가 나타나도록 개선되었다.