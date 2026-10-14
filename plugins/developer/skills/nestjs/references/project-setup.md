# 프로젝트 설정 파일

새 프로젝트를 만들 때 맞출 설정. 버전 번호는 설치 시점의 최신 안정판을 쓴다. `main.ts`, 환경 변수 검사, 로거 설정, request id, 헬스 체크, swc 빌드, vitest + unplugin-swc 는 2026-10 에 NestJS 12, Fastify, TypeScript 6.0, Node 24 로 실행해 확인했다. Dockerfile 과 GitHub Actions 는 실행하지 않은 예시다.

## package.json

```json
{
    "type": "module",
    "packageManager": "pnpm@<버전>",
    "engines": { "node": ">=<활성 LTS 메이저>" },
    "scripts": {
        "build": "nest build",
        "start": "UV_THREADPOOL_SIZE=16 node dist/main.js",
        "start:dev": "UV_THREADPOOL_SIZE=16 nest start --watch",
        "lint": "eslint .",
        "typecheck": "tsc --noEmit",
        "test": "vitest run --exclude \"test/**\"",
        "test:int": "vitest run test",
        "db:generate": "prisma generate",
        "db:validate": "prisma validate",
        "postinstall": "prisma generate",
        "prepare": "husky"
    }
}
```

- TypeScript 는 `~6.0.0` 으로 고정한다. 그냥 설치하면 TypeScript 7 이 들어오는데, typescript-eslint(8.71 기준)가 `<6.1.0` 만 지원해 타입 기반 린트가 동작하지 않는다.
- Node 버전은 `.nvmrc` 에 활성 LTS 메이저(예: `24`)로 고정하고 `engines.node` 와 맞춘다. CI 도 `.nvmrc` 를 읽는다.
- Dockerfile 로 배포하면 `ENV UV_THREADPOOL_SIZE=16` 으로 넣는다.
- pnpm 10 이상은 의존성의 설치 스크립트를 막는다. `pnpm approve-builds` 로 `prisma`, `@prisma/engines`, `@swc/core` 등 필요한 것만 승인한다.
- 모노레포에서는 `postinstall` 대신 Turborepo 태스크 의존성으로 `db:generate` 를 먼저 돌린다.

## tsconfig.json

```json
{
    "compilerOptions": {
        "module": "NodeNext",
        "moduleResolution": "NodeNext",
        "target": "ES2023",
        "strict": true,
        "experimentalDecorators": true,
        "emitDecoratorMetadata": true,
        "skipLibCheck": true,
        "types": ["node"],
        "sourceMap": true,
        "outDir": "dist"
    },
    "include": ["src", "test"]
}
```

- TypeScript 6 부터 `types` 기본값이 빈 배열이라 `@types/node` 를 설치하고 `"types": ["node"]` 를 명시한다. 테스트에서 vitest 전역을 쓰지 않으므로 `vitest/globals` 는 넣지 않는다.
- `verbatimModuleSyntax` 는 켜지 않는다. 생성자 주입 타입의 import 가 바뀌어 DI 메타데이터가 깨질 수 있다.

## tsconfig.build.json

`nest build` 가 테스트 파일을 `dist` 에 넣지 않게 뺀다.

```json
{
    "extends": "./tsconfig.json",
    "exclude": ["node_modules", "dist", "test", "**/*.spec.ts"]
}
```

## main.ts

```ts
import "reflect-metadata";

import { type IncomingMessage } from "node:http";

import helmet from "@fastify/helmet";
import { ConfigService } from "@nestjs/config";
import { NestFactory } from "@nestjs/core";
import { FastifyAdapter, type NestFastifyApplication } from "@nestjs/platform-fastify";
import { Logger } from "nestjs-pino";

import { AppModule } from "./app.module.js";
import { RequestId } from "./common/request-id.js";

const proxyHops = Number(process.env["TRUST_PROXY_HOPS"] ?? "0");
const adapter = new FastifyAdapter({
    requestIdHeader: false,
    genReqId: (req: IncomingMessage) => RequestId.from(req.headers["x-request-id"]),
    trustProxy: (_address: string, hop: number) => hop < proxyHops,
});
const app = await NestFactory.create<NestFastifyApplication>(AppModule, adapter, { bufferLogs: true });
app.useLogger(app.get(Logger));
await app.register(helmet);
app.enableShutdownHooks();
// ValidationPipe, 전역 ExceptionFilter, CORS 설정을 여기에 둔다. Swagger 는 APP_ENV 가 production 이 아닐 때만 설정한다.
await app.listen(app.get(ConfigService).getOrThrow<number>("PORT"), "0.0.0.0");
```

- Fastify 는 request id 를 직접 만든다. pino 가 아니라 `FastifyAdapter` 의 `genReqId` 로 정해야 로그에 반영된다. `requestIdHeader: false` 로 Fastify 가 헤더 값을 검사 없이 쓰지 않게 막고, `RequestId.from` 으로 형식을 검사한다. 형식에 맞는 `ok-123` 은 그대로, 공백이 든 값은 UUID 로 바뀌는 것을 확인했다.
- `TRUST_PROXY_HOPS` 는 앞단 프록시 수다(로드밸런서 하나면 `1`, 없으면 `0`). 프록시가 없는 환경에서 `trustProxy` 를 켜면 클라이언트가 `X-Forwarded-For` 로 IP 를 위조할 수 있다. Nest 의 `FastifyAdapter` 타입은 `trustProxy` 에 숫자를 받지 않으므로 함수로 준다. 어댑터는 `ConfigService` 보다 먼저 만들어지므로 여기서만 `process.env` 를 읽는다.
- 컨테이너에서 받으려면 `0.0.0.0` 에 바인딩한다.

## app.module.ts

```ts
@Module({
    imports: [
        ConfigModule.forRoot({
            isGlobal: true,
            envFilePath: [`.env.${process.env["APP_ENV"] ?? "local"}`, ".env"],
            validate: (raw) => Environment.validate(raw),
        }),
        LoggerModule.forRootAsync({
            inject: [ConfigService],
            useFactory: (config: ConfigService) => LoggerConfig.create(config),
        }),
        ClsModule.forRoot({ global: true, middleware: { mount: true } }),
        TerminusModule,
    ],
    controllers: [HealthController],
})
class AppModule {}

export { AppModule };
```

`ClsModule` 은 트랜잭션(`@Transactional()`)에 쓴다. 트랜잭션 플러그인(`ClsPluginTransactional`)을 같은 `ClsModule.forRoot` 에 등록한다.

## src/common/request-id.ts

```ts
import { randomUUID } from "node:crypto";

class RequestId {
    private static readonly VALID = /^[A-Za-z0-9-]{1,64}$/;

    public static from(header: string | string[] | undefined): string {
        return typeof header === "string" && RequestId.VALID.test(header) ? header : randomUUID();
    }
}

export { RequestId };
```

## src/health/health.controller.ts

DB 확인은 `PrismaHealthIndicator` 의 `pingCheck("database", prisma)` 를 `check([...])` 에 넣는다.

```ts
import { Controller, Get } from "@nestjs/common";
import { HealthCheck, type HealthCheckResult, HealthCheckService } from "@nestjs/terminus";

@Controller("health")
class HealthController {
    constructor(private readonly health: HealthCheckService) {}

    @Get()
    @HealthCheck()
    public async check(): Promise<HealthCheckResult> {
        return this.health.check([]);
    }
}

export { HealthController };
```

## src/config/environment.ts

시작할 때 환경 변수를 검사한다. 값이 틀리면 `환경 변수 오류: PORT` 처럼 실패하고 서버가 뜨지 않는다.

```ts
import { plainToInstance, Type } from "class-transformer";
import { IsIn, IsInt, IsOptional, Max, Min, validateSync } from "class-validator";

class Environment {
    @IsIn(["local", "develop", "production"])
    public APP_ENV: "local" | "develop" | "production" = "local";

    @Type(() => Number)
    @IsInt()
    @Min(1)
    @Max(65535)
    public PORT = 3000;

    @IsOptional()
    @IsIn(["fatal", "error", "warn", "info", "debug", "trace"])
    public LOG_LEVEL?: string;

    public static validate(raw: Record<string, unknown>): Environment {
        const environment = plainToInstance(Environment, raw, { enableImplicitConversion: true });
        const errors = validateSync(environment, { skipMissingProperties: false });
        if (errors.length > 0) {
            throw new Error(`환경 변수 오류: ${errors.map((error) => error.property).join(", ")}`);
        }
        return environment;
    }
}

export { Environment };
```

## src/config/logger.config.ts

```ts
import { ConfigService } from "@nestjs/config";
import { type Params } from "nestjs-pino";
import { stdTimeFunctions } from "pino";

class LoggerConfig {
    public static create(config: ConfigService): Params {
        const production = config.get<string>("APP_ENV") === "production";
        return {
            pinoHttp: {
                level: config.get<string>("LOG_LEVEL") ?? (production ? "info" : "debug"),
                timestamp: stdTimeFunctions.isoTime,
                redact: ["req.headers.authorization", "req.headers.cookie", "res.headers[\"set-cookie\"]"],
                customProps: () => ({ context: "HTTP" }),
                customSuccessMessage: (req, res, responseTime) => `${req.method} ${req.url} ${res.statusCode} ${responseTime}ms`,
                customErrorMessage: (req, res) => `${req.method} ${req.url} ${res.statusCode}`,
                transport: production ? undefined : LoggerConfig.prettyTransport(),
            },
        };
    }

    private static prettyTransport(): { target: string; options: Record<string, unknown> } {
        return {
            target: "pino-pretty",
            options: {
                colorize: true,
                singleLine: true,
                translateTime: "SYS:yyyy-mm-dd'T'HH:MM:ss.lp",
                ignore: "pid,hostname,context,req,res,responseTime",
                messageFormat: "{if req.id}[{req.id}] {end}{context} - {msg}",
            },
        };
    }
}

export { LoggerConfig };
```

`local`, `develop` 출력:

```
[2026-10-14T17:46:38.038+09:00] INFO: NestApplication - Nest application successfully started
[2026-10-14T17:46:41.687+09:00] INFO: [a613e7d1-409c-47fc-ad52-7e5011910aa6] ClockService - 한국 시간 오늘 0시 utc=2026-10-13T15:00:00Z
[2026-10-14T17:46:41.689+09:00] INFO: [a613e7d1-409c-47fc-ad52-7e5011910aa6] HTTP - GET /health 200 6ms
```

`production` 출력(JSON 한 줄):

```
{"level":30,"time":"2026-10-14T08:46:24.743Z","context":"HTTP","req":{"id":"d05fbb4e-...","method":"GET","url":"/health","headers":{"authorization":"[Redacted]"}},"msg":"GET /health 200 5ms"}
```

## 외부 API 클라이언트

`src/clients/payment/payment.client.ts`. `PAYMENT_API_URL`, `PAYMENT_API_TIMEOUT_MS` 는 `Environment` 에 추가해 검사한다.

```ts
import { BadGatewayException, GatewayTimeoutException, HttpException, Injectable, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import axios, { type AxiosInstance, isAxiosError } from "axios";

type PaymentResponse = {
    paymentId: string;
    amount: number;
};

@Injectable()
class PaymentClient {
    private readonly logger = new Logger(PaymentClient.name);

    private readonly http: AxiosInstance;

    constructor(config: ConfigService) {
        this.http = axios.create({
            baseURL: config.getOrThrow<string>("PAYMENT_API_URL"),
            timeout: config.getOrThrow<number>("PAYMENT_API_TIMEOUT_MS"),
        });
    }

    public async getPayment(paymentId: string): Promise<PaymentResponse> {
        try {
            const response = await this.http.get<PaymentResponse>(`/payments/${paymentId}`);
            return response.data;
        } catch (error) {
            throw this.toException(error);
        }
    }

    private toException(error: unknown): HttpException {
        if (isAxiosError(error) && error.code === "ECONNABORTED") {
            this.logger.warn(`결제 API 시간 초과 url=${error.config?.url}`);
            return new GatewayTimeoutException("결제 API 응답 시간 초과");
        }
        const status = isAxiosError(error) ? error.response?.status : undefined;
        this.logger.warn(`결제 API 실패 status=${status}`);
        return new BadGatewayException("결제 API 호출 실패");
    }
}

export { PaymentClient, type PaymentResponse };
```

확인한 동작: `timeout` 을 넘기면 504 로 응답한다. request id 는 외부 호출에 넘기지 않는다(`backend` 스킬 8절).

## Day.js

타임존 계산이 필요할 때만 쓴다. 플러그인 확장은 한 파일에서 한 번만 한다.

```ts
import dayjs from "dayjs";
import timezone from "dayjs/plugin/timezone.js";
import utc from "dayjs/plugin/utc.js";

dayjs.extend(utc);
dayjs.extend(timezone);

export { dayjs };
```

사용 예: `dayjs().tz("Asia/Seoul").startOf("day").toDate()` 는 한국 시간 오늘 0시를 `Date` 로 돌려준다.

## .env 파일

- `.env.local`, `.env.develop`, `.env.production` 에 프로필별 값을 두고, 공통값은 `.env` 에 둔다.
- `.gitignore` 에 `.env` 와 `.env.*` 를 넣고 `!.env.example` 로 예외를 둔다. 키 목록은 `.env.example` 로 커밋한다.

## .swcrc

```json
{
    "$schema": "https://swc.rs/schema.json",
    "sourceMaps": true,
    "module": { "type": "es6" },
    "jsc": {
        "target": "es2022",
        "parser": { "syntax": "typescript", "decorators": true, "dynamicImport": true },
        "transform": { "legacyDecorator": true, "decoratorMetadata": true },
        "keepClassNames": true
    }
}
```

## nest-cli.json

```json
{
    "$schema": "https://json.schemastore.org/nest-cli",
    "collection": "@nestjs/schematics",
    "sourceRoot": "src",
    "compilerOptions": {
        "builder": "swc",
        "typeCheck": true,
        "deleteOutDir": true
    }
}
```

## vitest.config.ts

vitest 기본 변환기(esbuild)는 데코레이터 메타데이터를 만들지 않으므로 `unplugin-swc` 가 필수다.

```ts
import swc from "unplugin-swc";
import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        root: "./",
        include: ["src/**/*.spec.ts", "test/**/*.int-spec.ts"],
    },
    plugins: [swc.vite({ module: { type: "es6" } })],
});
```

## prisma/schema.prisma

ESM 으로 생성되는 `prisma-client` 제너레이터를 쓰고 출력 경로를 지정한다. 드라이버 어댑터, `prisma.config.ts` 필요 여부는 설치한 Prisma 버전 문서를 확인한다.

```prisma
generator client {
    provider     = "prisma-client"
    output       = "../src/generated/prisma"
    moduleFormat = "esm"
}
```

`.gitignore` 에 `src/generated/` 를 추가한다.

## 트랜잭션 (nestjs-cls)

`AppModule` 에 `ClsModule` 을 등록하고 `ClsPluginTransactional` 에 `TransactionalAdapterPrisma` 를 연결한다. `prismaInjectionToken` 은 `PrismaService` 로 둔다. 정확한 옵션은 설치한 `@nestjs-cls/transactional` 버전 문서를 확인한다.

## Dockerfile

pnpm 과 `nest build` 기준 예시다. 실행해 보지 않은 예시다.

```dockerfile
FROM node:24-slim AS build
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build && pnpm prune --prod

FROM node:24-slim
ENV NODE_ENV=production TZ=Asia/Seoul UV_THREADPOOL_SIZE=16
WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./
USER node
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

- Prisma 를 쓰면 빌드 단계에서 `prisma generate` 가 돌아야 한다(`postinstall`). 생성된 클라이언트가 `dist` 나 `node_modules` 로 들어가는지 Prisma 버전 문서로 확인한다.

## GitHub Actions

`.github/workflows/ci.yml`. 실행해 보지 않은 예시다.

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
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm db:validate
      - run: pnpm lint
      - run: pnpm typecheck
      - run: pnpm test
      - run: pnpm test:int
```

## husky

```bash
pnpm add -D husky
pnpm exec husky init
```

`.husky/pre-push`:

```sh
pnpm db:validate
pnpm lint
pnpm typecheck
pnpm test
```

모노레포는 `pnpm turbo run db:validate lint typecheck test` 한 줄로 바꾼다. `husky init` 이 만든 `.husky/pre-commit` 은 지운다.

## 모노레포

`pnpm-workspace.yaml`:

```yaml
packages:
    - "apps/*"
    - "packages/*"
```

`turbo.json`:

```json
{
    "$schema": "https://turborepo.com/schema.json",
    "tasks": {
        "db:generate": { "cache": false },
        "db:validate": {},
        "build": { "dependsOn": ["^build", "db:generate"], "outputs": ["dist/**"] },
        "lint": { "dependsOn": ["^build"] },
        "typecheck": { "dependsOn": ["^build", "db:generate"] },
        "test": { "dependsOn": ["^build", "db:generate"] }
    }
}
```

- Nest 앱은 `apps/<이름>`, 공용 코드는 `packages/<이름>` 에 둔다.
- 각 패키지가 자기 `eslint.config.js`, `tsconfig.json`, `vitest.config.ts` 를 갖는다. 공통 설정은 `packages/config` 같은 패키지로 뽑아 가져다 쓴다.
