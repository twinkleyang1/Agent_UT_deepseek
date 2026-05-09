package com.hmdp.controller;

import com.hmdp.dto.LoginFormDTO;
import com.hmdp.dto.Result;
import com.hmdp.dto.UserDTO;
import com.hmdp.entity.User;
import com.hmdp.entity.UserInfo;
import com.hmdp.service.IUserInfoService;
import com.hmdp.service.IUserService;
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
import org.springframework.data.redis.core.StringRedisTemplate;

import javax.servlet.http.HttpSession;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class UserControllerTest {

    @Mock private IUserService userService;
    @Mock private IUserInfoService userInfoService;
    @Mock private StringRedisTemplate redisTemplate;
    @Mock private HttpSession session;
    @InjectMocks private UserController controller;

    @BeforeEach
    void setUp() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        user.setNickName("test");
        UserHolder.saveUser(user);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    void shouldSendCode() {
        when(userService.sendCode("13800138000", session)).thenReturn(Result.ok());

        Result result = controller.sendCode("13800138000", session);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldLogin() {
        LoginFormDTO form = LoginFormDTO.builder()
                .phone("13800138000").code("123456").password("pw").build();
        when(userService.login(form, session)).thenReturn(Result.ok("token123"));

        Result result = controller.login(form, session);

        assertTrue(result.getSuccess());
        assertEquals("token123", result.getData());
    }

    @Test
    void shouldLogout() {
        Result result = controller.logout();

        assertFalse(result.getSuccess());
        assertEquals("功能未完成", result.getErrorMsg());
        assertNull(UserHolder.getUser());
    }

    @Test
    void shouldGetCurrentUser() {
        // Re-save user since logout clears it
        UserDTO user = new UserDTO();
        user.setId(1L);
        UserHolder.saveUser(user);

        Result result = controller.me();

        assertTrue(result.getSuccess());
        assertEquals(1L, ((UserDTO) result.getData()).getId());
    }

    @Test
    void shouldGetUserInfo() {
        UserInfo info = new UserInfo();
        info.setUserId(2L);
        info.setCity("Shanghai");
        when(userInfoService.getById(2L)).thenReturn(info);

        Result result = controller.info(2L);

        assertTrue(result.getSuccess());
        UserInfo data = (UserInfo) result.getData();
        assertEquals("Shanghai", data.getCity());
    }

    @Test
    void shouldReturnOkWhenInfoNotFound() {
        when(userInfoService.getById(99L)).thenReturn(null);

        Result result = controller.info(99L);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldQueryUserById() {
        User user = new User();
        user.setId(2L);
        user.setNickName("user2");
        when(userService.getById(2L)).thenReturn(user);

        Result result = controller.queryUserById(2L);

        assertTrue(result.getSuccess());
        UserDTO data = (UserDTO) result.getData();
        assertEquals("user2", data.getNickName());
    }

    @Test
    void shouldReturnOkWhenUserNotFound() {
        when(userService.getById(99L)).thenReturn(null);

        Result result = controller.queryUserById(99L);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldSign() {
        when(userService.sign()).thenReturn(Result.ok());

        Result result = controller.sign();

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldSignCount() {
        when(userService.signCount()).thenReturn(Result.ok(5));

        Result result = controller.signCount();

        assertTrue(result.getSuccess());
        assertEquals(5, result.getData());
    }
}
