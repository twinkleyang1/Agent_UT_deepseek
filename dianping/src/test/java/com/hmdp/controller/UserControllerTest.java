package com.hmdp.controller;

import com.hmdp.dto.Result;
import com.hmdp.entity.UserInfo;
import com.hmdp.service.IUserInfoService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserControllerTest {

    @Mock
    private IUserInfoService userInfoService;

    private UserController controller;

    @BeforeEach
    void setUp() throws Exception {
        controller = new UserController();
        Field field = UserController.class.getDeclaredField("userInfoService");
        field.setAccessible(true);
        field.set(controller, userInfoService);
    }

    @Test
    void shouldReturnResultWhenInfo() {
        // Arrange
        Long userId = 1L;
        UserInfo info = new UserInfo();
        info.setUserId(userId);
        info.setCity("北京");
        info.setCreateTime(java.time.LocalDateTime.now());
        info.setUpdateTime(java.time.LocalDateTime.now());
        when(userInfoService.getById(userId)).thenReturn(info);

        // Act
        Result result = controller.info(userId);

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertNotNull(result.getData());
        UserInfo resultInfo = (UserInfo) result.getData();
        assertNull(resultInfo.getCreateTime());
        assertNull(resultInfo.getUpdateTime());
        assertEquals("北京", resultInfo.getCity());

        verify(userInfoService).getById(userId);
    }
}
