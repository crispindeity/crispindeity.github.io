---
title: (Spring)@ModelAttribute
date: 2022-12-16 12:30:00 +0900
modified: 2022-12-16 12:30:00 +0900
categories: [Spring]
tags: [Spring]
pin: false
---

# @ModelAttribute

## 글을 작성하게 된 이유
- N 사 모 카페에서 질문 글을 읽어 보던 중, 내가 생각했던 해결방법과 작성자께서 해결하신 해결 방법이 달라 헷갈렸던 내용을 정리하면서, `@ModelAttribute` 에 대해 정확하게 알고자 작성하게 되었다.
- 질문 내용으로는 Form 형식으로 데이터를 전송하는 중에 Dto 를 사용해서 전송된 값을 Controller 에서 받고 있는데 그 값이 null 로 들어온다는 내용이였다.

### 헷갈렸던 내용
```java
@Controller
public class Test {
    @RequestMapping(value = "/create", method = RequestMethod.POST)
    public String hospicreate(HosSaveRequestDto dto) {
        ...
        return "redirect:/";
    }
}
```
- HosSaveRequestDto 를 통해서 Form 에서 전달된 데이터를 받고있는데, 여기서 dto 내부의 값이 null 로 받아지는 문제가 발생하고 있었다.

```java
@Getter
@NoArgsConstructor
public class HosSaveRequestDto {
    private Long id;
    private String name;
    private String address;

    @Builder
    public HosSaveRequestDto(Long id, String name, String address) {
        this.id = id;
        this.name = name;
        this.address = address;
    }

    public Hospital toEntity() {
        return Hospital.builder()
                .id(id)
                .name(name)
                .address(address)
                .build();
    }

    @Override
    public String toString() {
        return
                "name::" + this.getName()
                        + "address::" + this.getAddress();

    }
}
```
- Dto 내부의 모습
- 내가 생각했던 해결 방법으로는, @ModelAttribute 어노테이션이 빠져서 이런 문제가 발생하는 것이라 생각했었다.
- 작성자께서 해결하신 방법은 Dto 에 @Setter 어노테이션을 달아 모든 필드값에 대한 Setter 를 만들어 해결 하셨다.
- 처음 해결하셨다는 글을 보고 매우 당황했다. 내가 알기로는 Setter 가 필요가 없을텐데 왜? Setter 를 만들어 줌으로 해결이 되었을까?
- 내가 잘못알고 있던 내용이 많은것 같아 공부하고 정리하기로 했다.

## 사용방법
```java
@Target({ElementType.PARAMETER, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface ModelAttribute {
    ...
}
```
- @ModelAttribute 는 Parameter 와 Method 두 가지 방식을 지원한다.

### Method
```java
@Controller
public class Test {
    @RequestMapping(value = "/create", method = RequestMethod.POST)
    public String hospicreate(@ModelAttribute HosSaveRequestDto dto) {
        ...
        return "redirect:/";
    }
    
    @ModelAttribute
    public void modelAttributeMethodTest() {
        System.out.println("method attribute");
    }
}
```
- Controller 에서 Method 에 명시하여 사용하면 된다.
- Method 에 @ModelAttribute 를 명시하여 사용할 경우 hospicreate Method 전에 @ModelAttribute 가 명시되어 있는 Method 가 먼저 실행되게 된다.

### Parameter
```java
@Controller
public class Test {
    @RequestMapping(value = "/create", method = RequestMethod.POST)
    public String hospicreate(@ModelAttribute HosSaveRequestDto dto) {
        ...
        return "redirect:/";
    }
}
```
- Controller 에서 파라미터 부분에 명시하여 사용하면 된다.

## 동작원리
### 순서
1. 생성자를 찾아서 인스턴스를 생성한다.
    1. public 으로 선언되어 있는 생성자를 찾는다.
        1. 만약 생성자가 없다면, public 이 아닌 생성자중 인자가 제일 적은 생성자를 선택
        2. 찾은 생성자가 1개라면, 해당 생성자를 선택
        3. 찾은 생성자가 여러 개라면, 인자수가 제일 적은 생성자를 선택
    2. 선택된 생성자를 사용해 인스턴스를 만들 때 생성자의 인자의 이름 중 클라이언트가 요청한 파라미터의 이름과 같은 것이 있다면 해당 인자에 요청한 파라미터의 값을 넣어서 생성
2. 클라이언트가 요청한 파라미터 기준으로 setter 메서드를 찾아서 setter 메서드를 찾아서 실행

### 상세
- @ModelAttribute 의 경우 ModelAttributeMethodProcessor 클래스 내부에서 대게 진행되며, constructAttribute 라는 이름의 메서드 내부에서 생성자를 찾는 동작이 이뤄진다.
```java
public class ModelAttributeMethodProcessor implements HandlerMethodArgumentResolver, HandlerMethodReturnValueHandler {
    protected Object constructAttribute(
        Constructor<?> ctor,
        String attributeName, MethodParameter parameter,
		WebDataBinderFactory binderFactory, 
		NativeWebRequest webRequest) throws Exception {
		if (ctor.getParameterCount() == 0) {
			// A single default constructor -> clearly a standard JavaBeans arrangement.
			return BeanUtils.instantiateClass(ctor);
		}
	...
	}
}
```
- 내부 로직이 매우 복잡 하지만, 하나씩 살펴본다면 위의 Dto(HosSaveRequestDto) 처럼 인자가 0개의 기본 생성자만 가지고 있는 경우라면, 여기서 보이는 if 문에 의해서 BeanUtils.instantiateClass(ctor) 로 넘어가게 된다.
- 여기서 setter 가 있는 경우와 없는 경우로 나뉘게 되는데.

```java
@Getter
@NoArgsConstructor
public class HosSaveRequestDto {
    private Long id;
    private String name;
    private String address;

    @Builder
    public HosSaveRequestDto(Long id, String name, String address) {
        this.id = id;
        this.name = name;
        this.address = address;
    }

    ...

    public void setName(String name) {
        this.name = name;
    }
}
```
- 이 처럼 setter 가 있을 경우 setter 를 이용해서 값을 넣어주게 된다.
- 만약 setter 가 없고 인자가 제일 적은 생성자가 기본 생성자일 경우 어떠한 값도 바인딩 시키지 못해 값을 넣어주지 못하게 된다.

```java
@Getter
public class HosSaveRequestDto {
    private Long id;
    private String name;
    private String address;

    @Builder
    public HosSaveRequestDto(Long id, String name, String address) {
        this.id = id;
        this.name = name;
        this.address = address;
    }

    ...
}
```
- 위의 경우 처럼 3개의 인자를 갖는 생성자가 유일한 생성자의 경우 생성자를 통해 값이 바인딩 되기 때문에 문제 없이 값이 잘 받아지게 된다.

## 생략 가능
```java
public class ModelAttributeMethodProcessor implements HandlerMethodArgumentResolver, HandlerMethodReturnValueHandler {
    @Override
	public boolean supportsParameter(MethodParameter parameter) {
		return (parameter.hasParameterAnnotation(ModelAttribute.class) ||
				(this.annotationNotRequired && !BeanUtils.isSimpleProperty(parameter.getParameterType())));
	}
}
```
- SimpleValueType 이 아니면서, Argument Resolver에 등록되어 있지 않는 경우 @ModelAttribute 가 사용된다.
- 즉, Parameter 의 Type 복합 타입일 경우 생략하여도 @ModelAttribute 가 동작하기 때문에 생략이 가능하다.
- 단, 코드의 가독성이나 추후 유지보수를 생각한다면 생략하는것 보다 명시해주는것이 좋다.

## 정리
- 위에 질문에 대해 해결하는 방법으로는 두 가지가 있다는걸 알게되었다.
- 첫번째로는 setter 를 사용하는 방법
    - Dto 라 크게 문제되지 않을것 같지만, 그래도 무분별한 setter 의 사용은 지양하는 편이 좋다.
- 두번째로는 생성자 를 사용하는 방법
    - 단, form 에서 넘겨주는 name 의 값과 생성자에 인자값의 이름과 동일하게 맞춰줘야 하며 2개 이상의 생성자가 있는 경우 주의해서 사용해줘야 한다.
- 위에 질문에서 가장 큰 문제점은 생성자를 2개 사용하는데 그 중 하나로 기본생성자를 사용하고 있다는 문제인것 같다. 만약 기본생성자를 절대적으로 사용해야만 한다면 바인딩 해줘야하는 필드값에 대해 setter 를 만들어주어야 할것 같다.