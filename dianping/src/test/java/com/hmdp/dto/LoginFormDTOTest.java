package com.hmdp.dto;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class LoginFormDTOTest {

    @Test
    void shouldBuildLoginFormDTOWithPhoneAndCode() {
        LoginFormDTO form = LoginFormDTO.builder()
                .phone("13800138000")
                .code("123456")
                .build();

        assertEquals("13800138000", form.getPhone());
        assertEquals("123456", form.getCode());
        assertNull(form.getPassword());
    }

    @Test
    void shouldBuildLoginFormDTOWithPhoneAndPassword() {
        LoginFormDTO form = LoginFormDTO.builder()
                .phone("13800138000")
                .password("secret123")
                .build();

        assertEquals("13800138000", form.getPhone());
        assertEquals("secret123", form.getPassword());
        assertNull(form.getCode());
    }

    @Test
    void shouldBuildLoginFormDTOWithAllFields() {
        LoginFormDTO form = LoginFormDTO.builder()
                .phone("13800138000")
                .code("123456")
                .password("secret123")
                .build();

        assertEquals("13800138000", form.getPhone());
        assertEquals("123456", form.getCode());
        assertEquals("secret123", form.getPassword());
    }

    @Test
    void shouldBeEqualWhenSameFields() {
        LoginFormDTO form1 = LoginFormDTO.builder()
                .phone("13800138000")
                .code("123456")
                .password("secret")
                .build();
        LoginFormDTO form2 = LoginFormDTO.builder()
                .phone("13800138000")
                .code("123456")
                .password("secret")
                .build();

        assertEquals(form1, form2);
    }

}
