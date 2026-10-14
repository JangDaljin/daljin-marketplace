# 프로젝트 설정 파일

새 프로젝트를 만들 때 맞출 설정. 아래 버전은 2026-10 에 Java 25, Gradle 9.7 로 `./gradlew check` 통과를 확인한 조합이다. 새로 만들 때는 각 라이브러리의 최신 안정판으로 올리고 다시 확인한다.

## 디렉터리

```
.
├── settings.gradle.kts
├── gradle/libs.versions.toml
├── buildSrc/
│   ├── build.gradle.kts
│   └── src/main/kotlin/java-conventions.gradle.kts
├── config/checkstyle/google_checks.xml
├── .githooks/pre-push
├── api/build.gradle.kts
├── core/build.gradle.kts
└── infra/build.gradle.kts
```

## settings.gradle.kts

```kotlin
rootProject.name = "app"

include("api", "core", "infra")
```

## gradle/libs.versions.toml

```toml
[versions]
spring-boot = "4.1.1"
springdoc = "3.1.1"
querydsl = "7.7"

[libraries]
spring-boot-bom = { module = "org.springframework.boot:spring-boot-dependencies", version.ref = "spring-boot" }
springdoc = { module = "org.springdoc:springdoc-openapi-starter-webmvc-ui", version.ref = "springdoc" }
querydsl-jpa = { module = "io.github.openfeign.querydsl:querydsl-jpa", version.ref = "querydsl" }
querydsl-apt = { module = "io.github.openfeign.querydsl:querydsl-apt", version.ref = "querydsl" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
```

## buildSrc

`buildSrc/build.gradle.kts`:

```kotlin
plugins {
    `kotlin-dsl`
}

repositories {
    gradlePluginPortal()
}

dependencies {
    implementation("com.diffplug.spotless:spotless-plugin-gradle:8.10.4")
}
```

`buildSrc/src/main/kotlin/java-conventions.gradle.kts`:

```kotlin
plugins {
    java
    checkstyle
    id("com.diffplug.spotless")
}

repositories {
    mavenCentral()
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(25)
    }
}

checkstyle {
    toolVersion = "14.3.0"
    configFile = rootProject.file("config/checkstyle/google_checks.xml")
    maxWarnings = 0
}

spotless {
    java {
        googleJavaFormat()
    }
}

tasks.test {
    useJUnitPlatform {
        excludeTags("integration")
    }
}

val integrationTest by tasks.registering(Test::class) {
    description = "Testcontainers 통합 테스트"
    group = "verification"
    testClassesDirs = sourceSets.test.get().output.classesDirs
    classpath = sourceSets.test.get().runtimeClasspath
    useJUnitPlatform {
        includeTags("integration")
    }
}
```

- `googleJavaFormat()` 에 버전을 넣지 않고 Spotless 기본값을 쓴다. Spotless 8.10.4 에 google-java-format 1.37.0 을 지정하면 모든 파일에서 `InvocationTargetException` 으로 실패했다.
- `google_checks.xml` 은 `toolVersion` 과 같은 태그에서 받는다: `https://raw.githubusercontent.com/checkstyle/checkstyle/checkstyle-<버전>/src/main/resources/google_checks.xml`
- `maxWarnings = 0` 이 없으면 Google 설정의 위반이 경고로만 나오고 빌드가 통과한다.

## 모듈별 build.gradle.kts

`core/build.gradle.kts`:

```kotlin
plugins {
    id("java-conventions")
    `java-library`
}

dependencies {
    implementation(platform(libs.spring.boot.bom))
    annotationProcessor(platform(libs.spring.boot.bom))

    api("org.springframework.boot:spring-boot-starter-data-jpa")
    api(libs.querydsl.jpa)
    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")
    annotationProcessor(variantOf(libs.querydsl.apt) { classifier("jpa") })
    annotationProcessor("jakarta.persistence:jakarta.persistence-api")
}
```

`infra/build.gradle.kts`:

```kotlin
plugins {
    id("java-conventions")
}

dependencies {
    implementation(platform(libs.spring.boot.bom))

    implementation(project(":core"))
    implementation("org.springframework.boot:spring-boot-starter-liquibase")
    runtimeOnly("org.postgresql:postgresql")
}
```

`api/build.gradle.kts`:

```kotlin
plugins {
    id("java-conventions")
    alias(libs.plugins.spring.boot)
}

dependencies {
    implementation(platform(libs.spring.boot.bom))
    testImplementation(platform(libs.spring.boot.bom))
    annotationProcessor(platform(libs.spring.boot.bom))

    implementation(project(":core"))
    runtimeOnly(project(":infra"))
    implementation("org.springframework.boot:spring-boot-starter-webmvc")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation(libs.springdoc)
    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")

    testImplementation("org.springframework.boot:spring-boot-starter-webmvc-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
```

- Spring Boot 4 는 스타터가 기술별로 나뉘었다: `spring-boot-starter-webmvc`, `spring-boot-starter-webmvc-test`, `spring-boot-starter-liquibase`.
- Spring Boot 4 에서 `@WebMvcTest` 는 `org.springframework.boot.webmvc.test.autoconfigure` 패키지에 있다. Service 대체는 `@MockitoBean`(`org.springframework.test.context.bean.override.mockito`)을 쓴다. `@MockBean` 은 없다.
- 통합 테스트용 Testcontainers 의존성은 통합 테스트를 두는 모듈에 `testImplementation` 으로 추가한다.

## application.yml (api)

```yaml
spring:
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
  liquibase:
    change-log: classpath:db/changelog/db.changelog-master.yaml

app:
  cors:
    allowed-origins: ${CORS_ALLOWED_ORIGINS:}
```

Liquibase changelog 는 `infra/src/main/resources/db/changelog/` 에 둔다. `api` 가 `infra` 를 runtimeOnly 로 가지므로 실행 시 classpath 에 올라간다.

## Git 훅

`.githooks/pre-push`:

```sh
#!/bin/sh
./gradlew check
```

```bash
chmod +x .githooks/pre-push
git config core.hooksPath .githooks
```
