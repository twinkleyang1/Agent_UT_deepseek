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
import java.util.Collections;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class UserServiceImplTest {

    @Mock private UserMapper baseMapper;
    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private ValueOperations<String, String> valueOps;
    @Mock private HashOperations<String, Object, Object> hashOps;
    @Mock private HttpSession session;
    @InjectMocks private UserServiceImpl service;

    @BeforeEach
    void setUp() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        UserHolder.saveUser(user);
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
        when(stringRedisTemplate.opsForHash()).thenReturn(hashOps);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    void shouldSendCodeWithValidPhone() {
        Result result = service.sendCode("13800138000", session);

        assertTrue(result.getSuccess());
        verify(valueOps).set(contains("login:code:"), anyString(), eq(2L), eq(TimeUnit.MINUTES));
    }

    @Test
    void shouldFailSendCodeWithInvalidPhone() {
        Result result = service.sendCode("12345", session);

        assertFalse(result.getSuccess());
        assertEquals("手机号格式错误", result.getErrorMsg());
    }

    @Test
    void shouldFailLoginWithInvalidPhone() {
        LoginFormDTO form = LoginFormDTO.builder()
                .phone("12345").code("123456").password("pw").build();

        Result result = service.login(form, session);

        assertFalse(result.getSuccess());
        assertEquals("手机号格式错误", result.getErrorMsg());
    }

    @Test
    void shouldFailLoginWithWrongCode() {
        LoginFormDTO form = LoginFormDTO.builder()
                .phone("13800138000").code("123456").password("pw").build();
        when(valueOps.get(contains("login:code:"))).thenReturn("654321");

        Result result = service.login(form, session);

        assertFalse(result.getSuccess());
        assertEquals("验证码不一致，请重新输入", result.getErrorMsg());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldLoginExistingUser() {
        LoginFormDTO form = LoginFormDTO.builder()
                .phone("13800138000").code("123456").password("pw").build();
        when(valueOps.get(contains("login:code:"))).thenReturn("123456");
        User user = new User();
        user.setId(1L);
        user.setPhone("13800138000");
        user.setNickName("test");
        when(baseMapper.selectOne(any(Wrapper.class))).thenReturn(user);
        when(stringRedisTemplate.expire(anyString(), eq(30L), eq(TimeUnit.MINUTES))).thenReturn(true);

        Result result = service.login(form, session);

        assertTrue(result.getSuccess());
        assertNotNull(result.getData());
    }

    @Test
    void shouldSign() {
        Result result = service.sign();

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldReturnSignCount() {
        List<Long> bitFieldResult = List.of(7L);
        when(valueOps.bitField(anyString(), any(BitFieldSubCommands.class))).thenReturn(bitFieldResult);

        Result result = service.signCount();

        assertTrue(result.getSuccess());
        assertEquals(3, result.getData());
    }

    @Test
    void shouldReturnZeroSignCountWhenNoResult() {
        when(valueOps.bitField(anyString(), any(BitFieldSubCommands.class))).thenReturn(Collections.emptyList());

        Result result = service.signCount();

        assertTrue(result.getSuccess());
        assertEquals(0, result.getData());
    }

    @Test
    void shouldReturnZeroSignCountWhenNullResult() {
        when(valueOps.bitField(anyString(), any(BitFieldSubCommands.class))).thenReturn(null);

        Result result = service.signCount();

        assertTrue(result.getSuccess());
        assertEquals(0, result.getData());
    }
}
