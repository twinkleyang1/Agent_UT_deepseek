package com.hmdp.utils;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PasswordEncoderTest {

    @Test
    void shouldMatchesSuccessfully() {
        // Arrange
        String rawPassword = "myPassword123";

        // Use encode() to generate encodedPassword with a random salt
        String encodedPassword = PasswordEncoder.encode(rawPassword);

        // Act
        Boolean result = PasswordEncoder.matches(encodedPassword, rawPassword);

        // Assert
        assertTrue(result, "matches should return true for correct password");
    }
}
