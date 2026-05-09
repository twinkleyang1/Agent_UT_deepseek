# Java UT 测试编写规范

## 一、UT 测试流程

### 1.1 测试金字塔

```
                    ┌─────────────┐
                    │  端到端测试  │   (E2E)
                    │    (E2E)    │
                    ├─────────────┤
                    │ 集成测试    │   (Integration)
                    │ (Integration)│
                    ├─────────────┤
                    │ 单元测试    │   (Unit) ← UT
                    │   (Unit)    │
                    └─────────────┘
```

### 1.2 标准流程

1. **需求分析** → 分析被测代码功能、边界条件、异常处理
2. **测试设计** → 遵循 AAA 原则 (Arrange-Act-Assert)，设计测试用例
3. **测试编写** → 使用 JUnit 5 + Mockito 编写测试
4. **测试执行** → 运行测试，确保通过
5. **覆盖率分析** → 使用 JaCoCo 分析代码覆盖率

---

## 二、测试用例设计原则

### 2.1 AAA 原则

```java
@Test
void shouldReturnUserWhenUserExists() {
    // Arrange - 准备测试数据和依赖
    User expected = new User("1", "Alice");
    when(userRepository.findById("1")).thenReturn(expected);

    // Act - 执行被测试方法
    User result = userService.getUser("1");

    // Assert - 验证结果
    assertNotNull(result);
    assertEquals("Alice", result.getName());
    verify(userRepository).findById("1");
}
```

### 2.2 测试覆盖类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 正常路径 | 验证基本功能 | `add(1, 2) = 3` |
| 边界条件 | null、0、空集合、最大值 | `add(null, 1)` 抛出异常 |
| 异常路径 | 验证异常处理 | `add(-1, 1)` 抛出 IllegalArgumentException |
| 错误处理 | 验证错误恢复 | 网络超时重试机制 |

### 2.3 命名规范

```java
// 测试类命名: [被测类名]Test 或 [被测类名]Tests
class UserServiceTest {
    // 测试方法命名: should[ExpectedBehavior]When[Condition]
    @Test
    void shouldReturnUserWhenUserExists() { }
    
    @Test
    void shouldThrowExceptionWhenIdIsNull() { }
    
    @Test
    void shouldReturnEmptyListWhenNoUsersExist() { }
}
```

---

## 三、技术栈与依赖

### 3.1 Maven 依赖 (JUnit 5)

```xml
<dependencies>
    <!-- JUnit 5 -->
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.0</version>
        <scope>test</scope>
    </dependency>

    <!-- Mockito -->
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-junit-jupiter</artifactId>
        <version>5.8.0</version>
        <scope>test</scope>
    </dependency>

    <!-- Mockito Inline (支持静态方法Mock) -->
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-inline</artifactId>
        <version>5.8.0</version>
        <scope>test</scope>
    </dependency>

    <!-- AssertJ (流畅断言) -->
    <dependency>
        <groupId>org.assertj</groupId>
        <artifactId>assertj-core</artifactId>
        <version>3.24.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### 3.2 目录结构

```
src/
├── main/java/...           # 生产代码
│   └── com/example/service/
│       └── UserService.java
└── test/java/...           # 测试代码 (与生产代码包结构一致)
    └── com/example/service/
        └── UserServiceTest.java
```

---

## 四、JUnit 5 注解

### 4.1 生命周期注解

| 注解 | 说明 |
|------|------|
| `@Test` | 标记测试方法 |
| `@BeforeEach` | 每个测试方法前执行 |
| `@AfterEach` | 每个测试方法后执行 |
| `@BeforeAll` | 所有测试前执行一次 (需 static) |
| `@AfterAll` | 所有测试后执行一次 (需 static) |
| `@Disabled` | 禁用测试类或方法 |
| `@DisplayName` | 自定义测试显示名称 |
| `@Nested` | 嵌套测试类 |

### 4.2 Mockito 注解

| 注解 | 说明 |
|------|------|
| `@Mock` | 创建 Mock 对象 |
| `@InjectMocks` | 注入 Mock 到被测对象 |
| `@Spy` | 创建真实对象，部分方法可 Mock |
| `@Captor` | 捕获方法参数 |

### 4.3 代码示例

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @BeforeEach
    void setUp() {
        // 初始化 Mock
    }

    @Test
    @DisplayName("Should return user when user exists")
    void shouldReturnUserWhenUserExists() {
        // given
        User expected = new User("1", "Alice");
        when(userRepository.findById("1")).thenReturn(expected);

        // when
        User result = userService.getUser("1");

        // then
        assertEquals("Alice", result.getName());
    }

    @Test
    void shouldThrowExceptionWhenIdIsNull() {
        assertThrows(IllegalArgumentException.class, 
            () -> userService.getUser(null));
    }
}
```

---

## 五、常用断言

### 5.1 基本断言

```java
assertEquals(expected, actual);      // 相等
assertNotEquals(expected, actual);   // 不等
assertNotNull(result);               // 不为 null
assertNull(result);                  // 为 null
assertTrue(condition);               // 为 true
assertFalse(condition);              // 为 false
assertSame(expected, actual);        // 同一对象 (same reference)
assertArrayEquals(expected, actual); // 数组相等
```

### 5.2 异常断言

```java
// 方式1: Lambda 方式 (推荐)
assertThrows(IllegalArgumentException.class, 
    () -> userService.getUser(null));

// 方式2: AssertThrows 方式
assertThrows(IllegalArgumentException.class, () -> {
    throw new IllegalArgumentException("Invalid id");
});
```

### 5.3 AssertJ 流畅断言

```java
import static org.assertj.core.api.Assertions.assertThat;

assertThat(user.getName())
    .isNotNull()
    .isEqualTo("Alice")
    .contains("Ali")
    .doesNotContain("Bob");

assertThat(users)
    .hasSize(3)
    .extracting(User::getName)
    .containsExactly("Alice", "Bob", "Carol");
```

---

## 六、Mock 使用规范

### 6.1 设置返回值

```java
// 基本返回
when(mock.findById("1")).thenReturn(user);

// 多个返回值
when(mock.findById("1"))
    .thenReturn(user1)
    .thenReturn(user2);

// 抛出异常
when(mock.findById("1")).thenThrow(new RuntimeException("Not found"));

// 使用 Lambda
when(mock.findById(anyString())).thenAnswer(invocation -> {
    String id = invocation.getArgument(0);
    return new User(id, "User-" + id);
});
```

### 6.2 验证调用

```java
// 验证调用次数
verify(mock, times(1)).findById("1");
verify(mock, atLeastOnce()).findById("1");
verify(mock, atMost(3)).findById("1");
verify(mock, never()).findById("99");  // 从未调用

// 验证调用顺序
InOrder inOrder = inOrder(mock1, mock2);
inOrder.verify(mock1).save(user);
inOrder.verify(mock2).sendNotification(user);
```

### 6.3 参数匹配

```java
when(mock.save(any(User.class))).thenReturn(true);
when(mock.findById(eq("1"))).thenReturn(user);

// 复杂匹配
when(mock.findById(argThat(id -> id != null && id.length() > 3)))
    .thenReturn(user);
```

---

## 七、覆盖率标准

### 7.1 覆盖率目标

| 指标 | 最低目标 | 良好目标 | 优秀目标 |
|------|----------|----------|----------|
| 行覆盖率 | 70% | 80% | 90% |
| 分支覆盖率 | 60% | 70% | 80% |
| 方法覆盖率 | 80% | 90% | 95% |

### 7.2 JaCoCo 配置

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.11</version>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
        <execution>
            <id>check</id>
            <goals>
                <goal>check</goal>
            </goals>
            <configuration>
                <rules>
                    <rule>
                        <element>METHOD</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.70</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

---

## 八、评价标准

### 8.1 好的 UT 特征

- ✅ **单一职责** - 每个测试只验证一个行为
- ✅ **命名清晰** - 方法名描述测试意图
- ✅ **AAA 结构** - Arrange-Act-Assert 分段清晰
- ✅ **边界覆盖** - 包含正常、边界、异常情况
- ✅ **独立无依赖** - 测试之间互不影响
- ✅ **可重复执行** - 多次运行结果一致
- ✅ **快速执行** - 单个单元测试 < 100ms

### 8.2 差的 UT 特征

- ❌ 测试关注实现细节而非行为
- ❌ 依赖特定执行顺序
- ❌ 包含外部依赖 (数据库、网络)
- ❌ 使用随机值作为断言
- ❌ 测试代码重复
- ❌ 缺少断言或断言不足
- ❌ 测试私有方法

### 8.3 测试质量检查表

```
□ 测试是否通过？
□ 测试是否测试了预期行为而非实现？
□ 测试是否覆盖了边界条件？
□ 测试是否相互独立？
□ 测试是否能快速执行？
□ 测试命名是否清晰？
□ 是否有适当的断言？
□ Mock 使用是否正确？
□ 代码覆盖率是否达标？
□ 测试是否可维护？
```

---

## 九、TDD 流程 (推荐)

```
┌─────────────────────────────────────┐
│  1. Red  - 编写一个失败的测试        │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│  2. Green - 编写最小代码使测试通过   │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│  3. Refactor - 重构代码和测试        │
└─────────────┬───────────────────────┘
              │
              └────── 继续下一个测试 ──▶
```

---

## 十、常见陷阱

1. **不要测试私有方法** - 通过公共 API 间接测试
2. **不要 Mock 静态方法** - 考虑重新设计
3. **不要在测试中写业务逻辑** - 测试应简洁
4. **不要忽略边界条件** - null、0、空集合等
5. **不要假设测试顺序** - 测试应相互独立
6. **不要使用 Thread.sleep** - 使用 Awaitility 等待异步

---

## 十一、Spring Boot 测试集成

### 11.1 依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

### 11.2 测试类型

| 注解 | 类型 | 说明 |
|------|------|------|
| `@SpringBootTest` | 集成测试 | 加载完整 Spring 上下文 |
| `@WebMvcTest` | 切片测试 | 只加载 Web 层 |
| `@DataJpaTest` | 切片测试 | 只加载 JPA |
| `@MockBean` | Mock | 在 Spring 容器中 Mock Bean |
| `@TestConfiguration` | 配置 | 自定义测试配置 |

### 11.3 示例

```java
@SpringBootTest
class UserServiceIntegrationTest {

    @Autowired
    private UserService userService;

    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldSaveAndRetrieveUser() {
        User user = new User("1", "Alice");
        userRepository.save(user);

        User result = userService.getUser("1");

        assertThat(result.getName()).isEqualTo("Alice");
    }
}

@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    void shouldReturnUser() throws Exception {
        when(userService.getUser("1"))
            .thenReturn(new User("1", "Alice"));

        mockMvc.perform(get("/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Alice"));
    }
}
```
