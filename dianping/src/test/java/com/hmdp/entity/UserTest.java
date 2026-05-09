package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class UserTest {

    @Test
    void shouldSetAndGetId() {
        User user = new User();
        user.setId(1L);
        assertEquals(1L, user.getId());
    }

    @Test
    void shouldSetAndGetPhone() {
        User user = new User();
        user.setPhone("13800138000");
        assertEquals("13800138000", user.getPhone());
    }

    @Test
    void shouldSetAndGetPassword() {
        User user = new User();
        user.setPassword("encrypted_pass");
        assertEquals("encrypted_pass", user.getPassword());
    }

    @Test
    void shouldSetAndGetNickName() {
        User user = new User();
        user.setNickName("Alice");
        assertEquals("Alice", user.getNickName());
    }

    @Test
    void shouldSetAndGetIcon() {
        User user = new User();
        user.setIcon("icon.png");
        assertEquals("icon.png", user.getIcon());
    }

    @Test
    void shouldSetAndGetCreateTime() {
        User user = new User();
        LocalDateTime now = LocalDateTime.now();
        user.setCreateTime(now);
        assertEquals(now, user.getCreateTime());
    }

    @Test
    void shouldSetAndGetUpdateTime() {
        User user = new User();
        LocalDateTime now = LocalDateTime.now();
        user.setUpdateTime(now);
        assertEquals(now, user.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        User user = new User()
                .setId(1L)
                .setPhone("13800138000")
                .setNickName("Alice");

        assertEquals(1L, user.getId());
        assertEquals("13800138000", user.getPhone());
        assertEquals("Alice", user.getNickName());
    }

    @Test
    void shouldHaveDefaultIconEmptyString() {
        User user = new User();
        assertEquals("", user.getIcon());
    }
}
