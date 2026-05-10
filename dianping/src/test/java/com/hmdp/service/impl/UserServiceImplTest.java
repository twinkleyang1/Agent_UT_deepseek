package com.hmdp.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.hmdp.dto.LoginFormDTO;
import com.hmdp.dto.Result;
import com.hmdp.dto.UserDTO;
import com.hmdp.entity.User;
import com.hmdp.mapper.UserMapper;
import com.hmdp.utils.UserHolder;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.connection.BitFieldSubCommands;
import org.springframework.data.redis.core.HashOperations;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import javax.servlet.http.HttpSession;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class UserServiceImplTest {

    @Mock
    private UserMapper baseMapper;

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    @Mock
    private HashOperations<String, Object, Object> hashOps;

    @InjectMocks
    private UserServiceImpl userService;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
        when(stringRedisTemplate.opsForHash()).thenReturn(hashOps);
    }

    @AfterEach
    void tearDown() {
        reset(baseMapper, stringRedisTemplate, valueOps, hashOps);
        UserHolder.removeUser();
    }

    @Test
    void shouldReturnResultWhenLogin() {
        // Arrange: valid phone and code
        String phone = "13800138000";
        String code = "123456";
        LoginFormDTO loginForm = LoginFormDTO.builder()
                .phone(phone)
                .code(code)
                .build();

        // Mock Redis: verification code matches
        when(valueOps.get("login:code:" + phone)).thenReturn(code);

        // Mock DB: user exists
        User user = new User()
                .setId(1L)
                .setPhone(phone)
                .setNickName("testUser")
                .setIcon("");
        when(baseMapper.selectOne(any(Wrapper.class))).thenReturn(user);

        // Act
        Result result = userService.login(loginForm, mock(HttpSession.class));

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertNotNull(result.getData());
        assertTrue(result.getData() instanceof String, "token should be a String");

        // Verify Redis hash storage was called
        verify(hashOps).putAll(startsWith("login:token:"), anyMap());
        verify(stringRedisTemplate).expire(startsWith("login:token:"), eq(30L), eq(TimeUnit.MINUTES));
    }

    @Test
    void shouldReturnResultWhenSignCount() {
        // Arrange: set up a logged-in user with ThreadLocal
        UserDTO userDTO = new UserDTO();
        userDTO.setId(1L);
        UserHolder.saveUser(userDTO);

        // Mock bitField: return bitmap 7 (binary 111) → 3 consecutive sign-in days
        List<Long> bitFieldResult = List.of(7L);
        when(valueOps.bitField(anyString(), any(BitFieldSubCommands.class)))
                .thenReturn(bitFieldResult);

        // Act
        Result result = userService.signCount();

        // Assert: should return 3 (consecutive trailing 1s in binary 111)
        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertEquals(3, result.getData());
    }
}
