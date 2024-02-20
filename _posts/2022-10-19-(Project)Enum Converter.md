---
title: (Project)Enum Converter
date: 2022-10-19 01:19:00 +0900
modified: 2022-10-19 01:19:00 +0900
categories: [Project]
tags: [Project]
pin: false
---

# Enum Converter

## 현재 상황
- `Controller` 와 `Request` 를 담당하는 `DTO` 에서 `Enum 타입` 을 사용하고 싶은데, `소문자`로 데이터가 들어올 경우 아래 문구의 예외가 발생하는 문제가 있다.
  `IllegalArgumentException: No enum constant team20.issuetracker.domain.issue.IssueStatus.open]`

- 왜 굳이 `Enum` 을 사용해야 하는가??
    - 웹 애플리케이션에서 데이터의 값을 사전에 정의된 값으로 제한을 하고 싶어서, Enum을 사용
    
    - 우리가 제한한 데이터 외의 값이 들어올 경우 예외 처리를 편리하게 할 수 있는 장점이 있다.
    
        

```java
public enum IssueStatus {
    OPEN, CLOSED;
}
```
- `IssueStatus` 의 경우 `OPEN` 이라는 값이 있지만 `소문자`로 들어온 `open` 과는 다른 값으로 취급 되고 있다.



## 문제 상황

### 첫번째 문제 상황

```java
@GetMapping(params = "is")
public ResponseEntity<ResponseReadAllIssueDto> readOpenAndClosedIssues(
    @RequestParam(value = "page", required = false, defaultValue = "1") String page,
    @RequestParam("is") IssueStatus status) 
{
    ...
}
```
- `Controller` 에서 `Enum` 으로 `@RequestParam` 데이터를 바인딩을 하려는 상황에서 `Query String` 으로 전달된 데이터가 `소문자`일 경우 바인딩 에러가 발생하고 있다.



### 두 번째 문제 상황

```java
@Getter
@NoArgsConstructor(access = AccessLevel.PRIVATE)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
public class RequestUpdateMilestoneDto {

    @NotEmpty
    @Size(max = 50, message = "Milestone 의 제목은 20글자를 넘을 수 없습니다.")
    private String title;

    @Size(max = 800, message = "Milestone 의 본문은 800글자를 넘을 수 없습니다.")
    private String description;

    @FutureOrPresent(message = "과거의 시간을 설정할 수는 없습니다.")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate dueDate;

    private MilestoneStatus milestoneStatus;

    public static RequestUpdateMilestoneDto of(String title, String description, LocalDate dueDate, MilestoneStatus milestoneStatus) {
        return new RequestUpdateMilestoneDto(title, description, dueDate, milestoneStatus);
    }
}
```
- 첫번째 상황과 비슷한 상황으로 이번에는 `Milestone` 을 `Update` 할때 현재 또는 변경되는 상태의 값을 받아야 하는데 이 값 또한 `Enum 타입` 으로 받고 있는 상황에서 데이터가 소문자로 들어 올 경우 바인딩 에러가 발생하고 있다.



## 문제 이유

```java
private static class StringToEnum<T extends Enum> implements Converter<String, T> {

	private final Class<T> enumType;

	StringToEnum(Class<T> enumType) {
		this.enumType = enumType;
	}

	@Override
	@Nullable
	public T convert(String source) {
		if (source.isEmpty()) {
			// It's an empty enum identifier: reset the enum value to null.
			return null;
		}
		return (T) Enum.valueOf(this.enumType, source.trim());
	}
}
```
- 스프링에서 기본적으로 제공해주는 `StringToEnum` 컨버터의 경우 위에 코드에 나와 있듯이 source 를 공백만 제거한 다음 별 다른 처리 없이 `valueOf` 를 해주고 있어 `소문자로 들어오면 그대로 소문자로`, `대문자로 들어오면 대문자로` 바인딩을 해주기 때문에 문제가 발생하고 있다.



## 해결 시도

### 첫번째 시도

- `프론트쪽`에서 소문자가 아닌 대문자로 데이터를 보내줄수 없는지 요청을 드렸었다 하지만, 여러 작업을 이미 소문자로 진행하였기 때문에 변경이 쉽지는 않다고 이야기를 하셔서 백엔드쪽에서 해결하도록 결정하였다.



### 두번째 시도

```java
@GetMapping(params = "is")
public ResponseEntity<ResponseReadAllIssueDto> readOpenAndClosedIssues(
    @RequestParam(value = "page", required = false, defaultValue = "1") String page,
    @RequestParam("is") String status) 
{
    ...
    ResponseReadAllIssueDto findOpenAndCloseIssues = issueService.findAllOpenAndCloseIssues
    (pageRequest, IssueStatus.valueOf(status.toUpperCase());
}
```
- 위에 문제가 되는 값을 String 으로 받은 후 `String.toUpperCase()` 를 사용해서 대문자로 변경한 뒤 `Enum` 에 적용 시키는 방법을 시도
- 위에 방법으로 해결이 가능하기는 했으나, `Enum` 을 사용하고자 했던 취지에는 벗어나기 때문에 다른 방법이 없나 다시 한번 찾아보기 시작했다.



### 세번째 시도

- 스프링 `기본 Converter` 를 사용하는 것이 아니라 `Custom Converter` 를 만들어서 사용

    

```java
public class StringToIssueStats implements Converter<String, IssueStatus> {
    @Override
    public IssueStatus convert(String status) {
        try {
            return IssueStatus.valueOf(status.toUpperCase());
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
```
- `Converter` 인터페이스를 구현하는 클래스 `StringToIssueStatus` 를 만들어서 `convert` 메서드를 `Override` 해서 내가 원하는 방식으로 변경하면 된다.

- 기존에는 별다른 처리 없이 `Enum.valueOf` 를 통해 데이터를 변환했다면, 지금은 `status` 라는 값이 들어올 경우 `toUpperCase()` 메서드를 사용해 대문자로 변경을 한 뒤 데이터를 변환하는 방식으로 진행되게끔 만들었다.

    

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(new StringToIssueStats());
    }
}
```
- 위에 클래스를 만든다고 해서 그냥 사용이 되는것은 아니고 Bean 으로 등록을 하거나 `Config 설정` 클래스에서 `Converter` 로 추가해주면 기존 `Converter` 가 아닌 내가 구현한 `Converter` 를 사용하게 된다.

- `Milestone Update` 또한 같은 방식으로 `Converter` 를 구현해서 사용하여 쉽게 해결 됐다.

    

---
## REFERENCE
- [Using Enums as Request Parameters in Spring](https://www.baeldung.com/spring-enum-request-param)