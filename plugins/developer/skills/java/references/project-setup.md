# 프로젝트 설정 파일

새 프로젝트를 만들 때 맞출 설정. 아래 버전과 설정은 2026-10 에 Java 25, Gradle 9.7 로 `./gradlew check` 통과를 확인한 조합이다(Log4j2 형식 출력, `@Value` 주입, JSpecify, id 조인 QueryDSL, Liquibase, 감사 컬럼, Testcontainers PostgreSQL 에서 `ZonedDateTime` 의 UTC 저장 포함). Dockerfile 과 GitHub Actions 는 실행하지 않은 예시다. 새로 만들 때는 각 라이브러리의 최신 안정판으로 올리고 다시 확인한다.

## 디렉터리

```
.
├── settings.gradle.kts
├── gradle/libs.versions.toml
├── buildSrc/
│   ├── build.gradle.kts
│   └── src/main/kotlin/java-conventions.gradle.kts
├── lombok.config
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
archunit = "1.5.1"

[libraries]
spring-boot-bom = { module = "org.springframework.boot:spring-boot-dependencies", version.ref = "spring-boot" }
springdoc = { module = "org.springdoc:springdoc-openapi-starter-webmvc-ui", version.ref = "springdoc" }
querydsl-jpa = { module = "io.github.openfeign.querydsl:querydsl-jpa", version.ref = "querydsl" }
querydsl-apt = { module = "io.github.openfeign.querydsl:querydsl-apt", version.ref = "querydsl" }
archunit = { module = "com.tngtech.archunit:archunit-junit5", version.ref = "archunit" }

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
    api("org.jspecify:jspecify")
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

configurations.all {
    exclude(group = "org.springframework.boot", module = "spring-boot-starter-logging")
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
    implementation("org.springframework.boot:spring-boot-starter-log4j2")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")

    testImplementation("org.springframework.boot:spring-boot-starter-webmvc-test")
    testImplementation(libs.archunit)
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.bootJar {
    archiveFileName = "app.jar"
}
```

- Spring Boot 4 는 스타터가 기술별로 나뉘었다: `spring-boot-starter-webmvc`, `spring-boot-starter-webmvc-test`, `spring-boot-starter-liquibase`.
- Spring Boot 4 에서 `@WebMvcTest` 는 `org.springframework.boot.webmvc.test.autoconfigure` 패키지에 있다. Service 대체는 `@MockitoBean`(`org.springframework.test.context.bean.override.mockito`)을 쓴다. `@MockBean` 은 없다.
- `org.jspecify:jspecify` 버전은 Spring Boot BOM 이 관리한다.
- 로깅 구현을 Log4j2 로 바꾸려고 모든 configuration 에서 `spring-boot-starter-logging` 을 뺀다.
- 여러 모듈이 테스트 fixture 를 공유하면 그 모듈에 `java-test-fixtures` 플러그인을 적용하고, 쓰는 쪽에서 `testImplementation(testFixtures(project(":core")))` 로 가져온다.
- 통합 테스트용 Testcontainers 의존성은 통합 테스트를 두는 모듈에 `testImplementation` 으로 추가한다.

## lombok.config

`@Value` 를 `final` 필드에 붙이고 `@RequiredArgsConstructor` 로 주입하려면 루트에 둔다.

```
lombok.copyableAnnotations += org.springframework.beans.factory.annotation.Value
```

## application.yml (api)

`application.yml` 은 공통값이다.

```yaml
spring:
  profiles:
    default: local
  threads:
    virtual:
      enabled: true
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        jdbc:
          time_zone: UTC
        timezone:
          default_storage: NORMALIZE_UTC
  jackson:
    time-zone: UTC
  liquibase:
    change-log: classpath:db/changelog/db.changelog-master.yaml
  datasource:
    password: ${DB_PASSWORD}
  lifecycle:
    timeout-per-shutdown-phase: 30s

server:
  shutdown: graceful

management:
  endpoints:
    web:
      exposure:
        include: health
  endpoint:
    health:
      show-details: never

app:
  error:
    include-stack: false
  cors:
    allowed-origins: ${CORS_ALLOWED_ORIGINS:}
```

`application-local.yml`, `application-develop.yml` 에서 개발용 값을 켠다. `application-production.yml` 에는 운영 값만 둔다.

```yaml
app:
  error:
    include-stack: true
```

`application-production.yml` 에서는 Swagger 를 끈다.

```yaml
springdoc:
  api-docs:
    enabled: false
  swagger-ui:
    enabled: false
```

Liquibase changelog 는 `infra/src/main/resources/db/changelog/` 에 둔다. `api` 가 `infra` 를 runtimeOnly 로 가지므로 실행 시 classpath 에 올라간다.

## log4j2-spring.xml (api)

`api/src/main/resources/log4j2-spring.xml`. 시각은 서버의 현재 시간(기본 타임존)에 오프셋을 붙여 찍고, `local`, `develop` 프로필에서만 애플리케이션 DEBUG 로그를 낸다. `com.example.app` 은 실제 최상위 패키지로 바꾼다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Configuration status="WARN">
  <Properties>
    <Property name="LOG_PATTERN">%d{yyyy-MM-dd'T'HH:mm:ss.SSSXXX} %-5level [%t] [%X{requestId}] %c{1.} - %m%n%throwable</Property>
  </Properties>

  <Appenders>
    <Console name="Console" target="SYSTEM_OUT">
      <PatternLayout pattern="${LOG_PATTERN}"/>
    </Console>
  </Appenders>

  <Loggers>
    <SpringProfile name="local | develop">
      <Logger name="com.example.app" level="DEBUG"/>
    </SpringProfile>
    <SpringProfile name="production">
      <Logger name="com.example.app" level="INFO"/>
    </SpringProfile>
    <Root level="INFO">
      <AppenderRef ref="Console"/>
    </Root>
  </Loggers>
</Configuration>
```

출력 예: `2026-10-14T18:02:54.527+09:00 INFO  [tomcat-handler-3] [trace-777] c.e.a.c.EventController - 이벤트 생성 occurredAt=2026-10-14T08:00Z`

- 컨테이너의 기본 타임존은 보통 UTC 다. 한국 시간으로 찍으려면 배포 환경에 `TZ=Asia/Seoul` 을 설정한다. DB 저장 시각은 이와 상관없이 UTC 다(`hibernate.jdbc.time_zone: UTC`).
- `requestId` 는 `RequestIdFilter` 가 MDC 에 채운다.

## Liquibase changelog

`infra/src/main/resources/db/changelog/db.changelog-master.yaml`:

```yaml
databaseChangeLog:
  - includeAll:
      path: db/changelog/changes/
```

`changes/20261014-01-create-event.yaml`. 코멘트(`remarks`), 기본 키와 인덱스 이름, `timestamptz`, 감사 컬럼을 넣은 예시다.

```yaml
databaseChangeLog:
  - changeSet:
      id: 20261014-01-create-event
      author: jangwonjin
      changes:
        - createTable:
            tableName: event
            remarks: 이벤트
            columns:
              - column:
                  name: id
                  type: bigint
                  autoIncrement: true
                  remarks: 이벤트 id
                  constraints:
                    primaryKey: true
                    primaryKeyName: pk_event
              - column:
                  name: occurred_at
                  type: timestamptz
                  remarks: 발생 시각
                  constraints:
                    nullable: false
              - column:
                  name: created_at
                  type: timestamptz
                  remarks: 생성 시각
                  constraints:
                    nullable: false
              - column:
                  name: updated_at
                  type: timestamptz
                  remarks: 수정 시각
                  constraints:
                    nullable: false
              - column:
                  name: created_by
                  type: bigint
                  remarks: 생성한 회원 id
              - column:
                  name: updated_by
                  type: bigint
                  remarks: 수정한 회원 id
        - createIndex:
            tableName: event
            indexName: idx_event_occurred_at
            columns:
              - column:
                  name: occurred_at
```

Entity id 는 `@GeneratedValue(strategy = GenerationType.IDENTITY)` 로 두고 컬럼은 `bigint` `autoIncrement: true` 로 만든다. 전략을 생략하면 Hibernate 가 `<테이블>_seq` 시퀀스를 찾아 changelog 와 맞지 않는다.

## 공통 코드

아래 코드는 `./gradlew check`(Checkstyle, Spotless, ArchUnit)와 Testcontainers PostgreSQL 통합 테스트를 통과했다. 통합 테스트에서 감사 컬럼이 UTC 로 채워지는 것, request id 가 로그에 찍히고 형식이 틀린 값은 UUID 로 바뀌는 것, 보안 헤더, 깨진 JSON 의 400 응답, `/actuator/health` 를 확인했다.

`core/.../entity/BaseEntity.java`:

```java
package com.example.app.entity;

import jakarta.persistence.Column;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.MappedSuperclass;
import java.time.ZonedDateTime;
import lombok.Getter;
import org.jspecify.annotations.Nullable;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

/** 감사 컬럼을 가진 Entity 의 공통 부모. */
@Getter
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseEntity {

  @CreatedDate
  @Column(nullable = false, updatable = false)
  private @Nullable ZonedDateTime createdAt;

  @LastModifiedDate
  @Column(nullable = false)
  private @Nullable ZonedDateTime updatedAt;

  @CreatedBy
  @Column(updatable = false)
  private @Nullable Long createdBy;

  @LastModifiedBy private @Nullable Long updatedBy;
}
```

`api/.../config/JpaAuditingConfig.java`. 인증을 붙이면 `auditorAware` 가 로그인 사용자 id 를 돌려주게 바꾼다.

```java
package com.example.app.config;

import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.Optional;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.auditing.DateTimeProvider;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

/** JPA 감사 설정. 시각은 UTC 로 채운다. */
@Configuration
@EnableJpaAuditing(dateTimeProviderRef = "utcDateTimeProvider")
public class JpaAuditingConfig {

  /** 감사 시각 공급자. */
  @Bean
  public DateTimeProvider utcDateTimeProvider() {
    return () -> Optional.of(ZonedDateTime.now(ZoneOffset.UTC));
  }

  /** 현재 사용자 id 공급자. 인증을 붙이면 로그인 사용자 id 를 돌려준다. */
  @Bean
  public AuditorAware<Long> auditorAware() {
    return Optional::empty;
  }
}
```

`api/.../config/RequestIdFilter.java`:

```java
package com.example.app.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;
import org.jspecify.annotations.Nullable;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** 요청마다 request id 를 정해 MDC 에 넣는다. */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdFilter extends OncePerRequestFilter {

  private static final String HEADER = "x-request-id";
  private static final String MDC_KEY = "requestId";
  private static final Pattern VALID = Pattern.compile("[A-Za-z0-9-]{1,64}");

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain chain)
      throws ServletException, IOException {
    MDC.put(MDC_KEY, resolve(request.getHeader(HEADER)));
    try {
      chain.doFilter(request, response);
    } finally {
      MDC.remove(MDC_KEY);
    }
  }

  private String resolve(@Nullable String header) {
    if (header != null && VALID.matcher(header).matches()) {
      return header;
    }
    return UUID.randomUUID().toString();
  }
}
```

`api/.../config/SecurityHeadersFilter.java`:

```java
package com.example.app.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** 응답에 보안 헤더를 붙인다. Spring Security 를 쓰면 그 기본 헤더를 대신 쓴다. */
@Component
public class SecurityHeadersFilter extends OncePerRequestFilter {

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain chain)
      throws ServletException, IOException {
    response.setHeader("X-Content-Type-Options", "nosniff");
    response.setHeader("X-Frame-Options", "DENY");
    response.setHeader("Referrer-Policy", "no-referrer");
    response.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
    chain.doFilter(request, response);
  }
}
```

`api/.../exception/ErrorResponse.java`, `GlobalExceptionHandler.java`. 비즈니스 예외, 외부 API 예외(502, 504) 처리는 프로젝트에 맞게 추가한다.

```java
package com.example.app.exception;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;
import org.jspecify.annotations.Nullable;

/** 에러 응답. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ErrorResponse(
    int statusCode, String message, List<FieldError> details, @Nullable String stack) {

  /** 필드별 오류. */
  public record FieldError(String field, String reason) {}
}
```

```java
package com.example.app.exception;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** 모든 예외를 에러 응답 형식으로 바꾼다. */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

  private final boolean includeStack;

  /** 생성자. */
  public GlobalExceptionHandler(@Value("${app.error.include-stack:false}") boolean includeStack) {
    this.includeStack = includeStack;
  }

  /** 요청 형식 검사 실패. */
  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<ErrorResponse> handleInvalid(MethodArgumentNotValidException e) {
    List<ErrorResponse.FieldError> details =
        e.getBindingResult().getFieldErrors().stream()
            .map(
                it ->
                    new ErrorResponse.FieldError(
                        it.getField(), String.valueOf(it.getDefaultMessage())))
            .toList();
    return respond(HttpStatus.BAD_REQUEST, "요청 형식이 올바르지 않습니다", details, e);
  }

  /** 요청 본문을 읽지 못함. */
  @ExceptionHandler(HttpMessageNotReadableException.class)
  public ResponseEntity<ErrorResponse> handleUnreadable(HttpMessageNotReadableException e) {
    return respond(HttpStatus.BAD_REQUEST, "요청 본문을 읽을 수 없습니다", List.of(), e);
  }

  /** 처리하지 못한 예외. */
  @ExceptionHandler(Exception.class)
  public ResponseEntity<ErrorResponse> handleUnknown(Exception e) {
    log.error("처리하지 못한 예외", e);
    return respond(HttpStatus.INTERNAL_SERVER_ERROR, "서버 오류가 발생했습니다", List.of(), e);
  }

  private ResponseEntity<ErrorResponse> respond(
      HttpStatus status, String message, List<ErrorResponse.FieldError> details, Exception e) {
    return ResponseEntity.status(status)
        .body(new ErrorResponse(status.value(), message, details, stackOf(e)));
  }

  private @Nullable String stackOf(Exception e) {
    if (!includeStack) {
      return null;
    }
    StringWriter writer = new StringWriter();
    e.printStackTrace(new PrintWriter(writer));
    return writer.toString();
  }
}
```

`api/src/test/java/.../architecture/LayerArchitectureTest.java`. Controller 가 Repository 를 쓰면 `Rule 'no classes that reside in a package '..controller..' should depend on classes that reside in a package '..repository..', because Controller 는 Service 만 부른다' was violated` 로 실패하는 것을 확인했다.

```java
package com.example.app.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

@AnalyzeClasses(packages = "com.example.app", importOptions = ImportOption.DoNotIncludeTests.class)
class LayerArchitectureTest {

  @ArchTest
  static final ArchRule CONTROLLER_DOES_NOT_USE_REPOSITORY =
      noClasses()
          .that()
          .resideInAPackage("..controller..")
          .should()
          .dependOnClassesThat()
          .resideInAPackage("..repository..")
          .because("Controller 는 Service 만 부른다");

  @ArchTest
  static final ArchRule CONTROLLER_DOES_NOT_USE_ENTITY =
      noClasses()
          .that()
          .resideInAnyPackage("..controller..", "..dto..")
          .should()
          .dependOnClassesThat()
          .resideInAPackage("..entity..")
          .because("Entity 를 API 로 내보내지 않는다");

  @ArchTest
  static final ArchRule API_DOES_NOT_USE_INFRA =
      noClasses()
          .that()
          .resideInAnyPackage("..controller..", "..dto..", "..config..", "..exception..")
          .should()
          .dependOnClassesThat()
          .resideInAPackage("..client..")
          .orShould()
          .dependOnClassesThat()
          .haveSimpleNameEndingWith("RepositoryImpl")
          .because("api 모듈은 infra 구현을 직접 참조하지 않는다");
}
```

## Dockerfile

Gradle wrapper(`./gradlew`)가 있다는 전제다. 테스트는 CI 에서 돌리므로 이미지 빌드에서는 뺀다. 이 Dockerfile 은 실행해 보지 않은 예시다.

```dockerfile
FROM eclipse-temurin:25-jdk AS build
WORKDIR /workspace
COPY . .
RUN ./gradlew :api:bootJar --no-daemon -x test

FROM eclipse-temurin:25-jre
ENV TZ=Asia/Seoul
WORKDIR /app
COPY --from=build /workspace/api/build/libs/app.jar app.jar
RUN useradd --system --uid 1001 app
USER app
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

## GitHub Actions

`.github/workflows/ci.yml`. GitHub 호스트 러너에는 Docker 가 있어 Testcontainers 통합 테스트가 돈다. 이 워크플로는 실행해 보지 않은 예시다.

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "25"
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew check integrationTest
```

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
