package com.hmdp.utils;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class PasswordEncoderTest {

    @Test
    void shouldEncodePasswordWithSalt() {
        String encoded = PasswordEncoder.encode("myPassword123");

        assertNotNull(encoded);
        assertTrue(encoded.contains("@"));
        String[] parts = encoded.split("@");
        assertEquals(2, parts.length);
        assertEquals(20, parts[0].length());
    }

    @Test
    void shouldEncodeDifferentPasswordsDifferently() {
        String encoded1 = PasswordEncoder.encode("password1");
        String encoded2 = PasswordEncoder.encode("password2");

        assertNotEquals(encoded1, encoded2);
    }

    @Test
    void shouldMatchWhenSamePassword() {
        String encoded = PasswordEncoder.encode("myPassword");

        assertTrue(PasswordEncoder.matches(encoded, "myPassword"));
    }

    @Test
    void shouldNotMatchWhenDifferentPassword() {
        String encoded = PasswordEncoder.encode("myPassword");

        assertFalse(PasswordEncoder.matches(encoded, "wrongPassword"));
    }

    @Test
    void shouldReturnFalseWhenEncodedPasswordIsNull() {
        assertFalse(PasswordEncoder.matches(null, "rawPassword"));
    }

    @Test
    void shouldReturnFalseWhenRawPasswordIsNull() {
        String encoded = PasswordEncoder.encode("password");
        assertFalse(PasswordEncoder.matches(encoded, null));
    }

    @Test
    void shouldThrowExceptionWhenEncodedPasswordHasNoAt() {
        assertThrows(RuntimeException.class, () ->
                PasswordEncoder.matches("no_at_sign", "password"));
    }

    @Test
    void shouldSamePasswordProduceSameMatchResult() {
        String encoded = PasswordEncoder.encode("samePass");
        assertTrue(PasswordEncoder.matches(encoded, "samePass"));
        assertTrue(PasswordEncoder.matches(encoded, "samePass"));
    }
}
