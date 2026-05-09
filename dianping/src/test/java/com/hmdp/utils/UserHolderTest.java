package com.hmdp.utils;

import com.hmdp.dto.UserDTO;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class UserHolderTest {

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    void shouldSaveAndGetUser() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        user.setNickName("Alice");

        UserHolder.saveUser(user);
        UserDTO result = UserHolder.getUser();

        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("Alice", result.getNickName());
    }

    @Test
    void shouldReturnNullWhenNoUserSaved() {
        assertNull(UserHolder.getUser());
    }

    @Test
    void shouldRemoveUser() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        UserHolder.saveUser(user);

        UserHolder.removeUser();

        assertNull(UserHolder.getUser());
    }

    @Test
    void shouldOverridePreviousUser() {
        UserDTO user1 = new UserDTO();
        user1.setId(1L);
        UserHolder.saveUser(user1);

        UserDTO user2 = new UserDTO();
        user2.setId(2L);
        UserHolder.saveUser(user2);

        assertEquals(2L, UserHolder.getUser().getId());
    }
}
