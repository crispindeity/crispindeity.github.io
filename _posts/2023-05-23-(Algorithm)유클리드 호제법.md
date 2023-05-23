---
title: (Algorithm)유클리드 호제법
author: crispin
date: 2023-05-23 12:47:00 +0900
modified: 2023-05-23 12:47:00 +0900
categories: [Algorithm]
tags: [Algorithm]
pin: false
---

## 유클리드 호제법?
- 두개의 자연수에 대한 최대 공약수를 구하는 알고리즘

## 원리

- 두 수의 자연수 `x` 와 `y` 에 대해 두 수를 나눈 나머지를 `z` 라고 했을때, `x` 와 `y` 의 최대 공약수는 `y` 와 `z` 의 최대 공약수와 같다.
- 위에 논리를 이용해서 `x` 와 `y` 의 나머지 `z` 를 구한 뒤 `y` 와 `z` 의 나머지 `z'` 를 구하여, `y` 와 `z'` 를 계속 나누다 나머지가 `0` 이 되는 순간의 `z'` 의 값이 `최대 공약수` 가 된다.

## 예

```textile
2, 16의 최대 공약수
 1) 12 % 16 = 12
 2) 16 % 12 = 4
 3) 12 % 4 = 0
 4) 최대 공약수 = 4 
```

## JAVA CODE

- 재귀와 유클리드 호제법을 사용해서 최대 공약수를 구하는 코드를 짜보자.

```java
public class GCD {
    public static void main() {
        int x = 12;
        int y = 16;
        int gcd = getGCD(x, y);
        System.out.println("gcd: " + gcd);
    }
    
    public static void getGCD(x, y) {
        if (x % y == 0) {
            return y;
        }
        return getGCD(y, x%y);
    }
}
```

## 최소 공배수는?

- 최소 공배수(LCM): (x * y) / 최대 공약수(GCD)
- 위에 공식을 활용하면 `최대 공약수(GCD)` 를 활용해서 `최소 공배수(LCM)` 도 쉽게 구할 수 있다.

## 자연수가 3개 이상일때는?

- 자연수 `x, y, z` 가 있다고 한다면, 먼저 `x와 y` 의 `최대 공약수(GCD)` 인 `f` 를 구한 뒤 `f와 z` 의 `최대 공약수(GCD)` 를 구하면 된다.

## 간단한 문제

- 프로그래머스에서 최대 공약수와 최소 공배수를 구하는 문제를 하나 풀어보자.
```java
class Solution {
    public int[] solution(int n, int m) {
        int[] answer = new int[2];
        int gcd = recursionFunction(n, m);
        int lcm = n * m / gcd;
        answer[0] = gcd;
        answer[1] = lcm;
        return answer;
    }

    public int recursionFunction(int n, int m) {
        if (n % m == 0) {
            return m;
        }
        return recursionFunction(m, n % m);
    }
}
```

-----

## REFERANCE

[유클리드 호제법](https://ko.wikipedia.org/wiki/유클리드_호제법)