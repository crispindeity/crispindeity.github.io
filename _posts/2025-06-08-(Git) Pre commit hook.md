---
title: (Git) Pre commit hook
date: 2025-06-08 15:00:00 +0900
modified: 2025-06-08 15:00:00 +0900
categories:
  - Git
tags:
  - Git
pin: false
---

## 📝 작성 배경
팀 프로젝트에서 코드 품질을 높이기 위한 방법은 여러 가지가 있습니다. 대중적으로 `CI` 에서 코드 품질을 높이기 위한 동작을 하게 되는데 `CI` 단계에서 `lint` 나 테스트에 실패하여 작업이 중단되는 경우가 종종 발생합니다. 하지만 이러한 방식은 작업 시간 측면이나 효율성 면에서 아쉬운 점이 있습니다. 이에 `CI` 이전 단계에서 개발자가 더 빠르게 피드백을 받고, 효율적으로 수정 및 작업할 수 있도록 도와주는 도구인 `pre commit hook` 을 소개해보려 합니다.

### 환경
글에 작성된 내용은 기본적으로 `mac` 환경에 대한 설명 입니다.

---
## 👓 선 3줄 요약
- A
- B
- C

---
## ❓ Pre commit
`pre commit hook` 은 `git commit` 전에 자동으로 특정 동작을 실행 시킬 수 있도록 설정하고 관리할 수 있게 해주는 도구 입니다.
`commit` 전에 동작을 하며, 주로 코드를 포맷팅 하거나 린트 검사, 테스트 수행, 파일 구조 확인, 보안 검사 등을 수행하며 코드 품질을 높이거나 유지할 수 있게 도와줍니다.
단, `pre commit hook` 만으로는 위에 나열되어 있는 동작을 하는건 아니며, 함께 사용할 툴이 필요합니다.

예를 들어
- `Python`: `black`
- `JS`: `eslint`, `prettier`
- `Kotlin`: `ktlinter`
- `Terraform`: `tfsec`
등이 있습니다.

---
## ⚙️ Setting
`pre commit hook` 을 설정하는 방법에는 여러가지가 있습니다.
1. 수동 설정 방식 사용
2. `pre-commit 도구 사용` 
3. `linter` 또는 라이브러리에서 제공하는 방식 사용

### 1. 수동 설정 방식 사용
`.git/hooks/pre-commit` 파일 생성 후 `commit` 전에 동작하길 원하는 동작들을 스크립트로 작성하면 쉽게 설정이 가능하다.
예를 들어 `kotlin` 프로젝트를 구성했는데, `commit` 전에 `ktlinter` 가 동작하게 하고 싶다면 아래와 같이 작성할 수 있다.
```bash
#!/bin/sh
set -e
./gradlew lintKotlin
```
물론 해당 프로젝트에 `ktlinter` 라이브러리에 대한 설정이 있어야 한다.
