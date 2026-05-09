package com.hmdp.dto;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class UserDTOTest {

    @Test
    void shouldSetAndGetId() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        assertEquals(1L, user.getId());
    }

    @Test
    void shouldSetAndGetNickName() {
        UserDTO user = new UserDTO();
        user.setNickName("Alice");
        assertEquals("Alice", user.getNickName());
    }

    @Test
    void shouldSetAndGetIcon() {
        UserDTO user = new UserDTO();
        user.setIcon("avatar.png");
        assertEquals("avatar.png", user.getIcon());
    }

    @Test
    void shouldCreateUserDTOWithAllFields() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        user.setNickName("Alice");
        user.setIcon("avatar.png");

        assertEquals(1L, user.getId());
        assertEquals("Alice", user.getNickName());
        assertEquals("avatar.png", user.getIcon());
    }
}
