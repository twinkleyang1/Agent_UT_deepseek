package com.hmdp.utils;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class RegexUtilsTest {

    @Test
    void shouldReturnFalseWhenPhoneIsValid() {
        assertFalse(RegexUtils.isPhoneInvalid("13800138000"));
    }

    @Test
    void shouldReturnTrueWhenPhoneIsInvalid() {
        assertTrue(RegexUtils.isPhoneInvalid("12345"));
    }

    @Test
    void shouldReturnTrueWhenPhoneIsNull() {
        assertTrue(RegexUtils.isPhoneInvalid(null));
    }

    @Test
    void shouldReturnTrueWhenPhoneIsBlank() {
        assertTrue(RegexUtils.isPhoneInvalid(""));
        assertTrue(RegexUtils.isPhoneInvalid("   "));
    }

    @Test
    void shouldReturnFalseWhenEmailIsValid() {
        assertFalse(RegexUtils.isEmailInvalid("test@example.com"));
    }

    @Test
    void shouldReturnTrueWhenEmailIsInvalid() {
        assertTrue(RegexUtils.isEmailInvalid("not-an-email"));
    }

    @Test
    void shouldReturnTrueWhenEmailIsBlank() {
        assertTrue(RegexUtils.isEmailInvalid(""));
        assertTrue(RegexUtils.isEmailInvalid(null));
    }

    @Test
    void shouldReturnFalseWhenCodeIsValid() {
        assertFalse(RegexUtils.isCodeInvalid("abc123"));
    }

    @Test
    void shouldReturnTrueWhenCodeIsTooShort() {
        assertTrue(RegexUtils.isCodeInvalid("123"));
    }
}
