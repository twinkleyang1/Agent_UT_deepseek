package com.hmdp.config;

import com.hmdp.dto.Result;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class WebExceptionAdviceTest {

    @Test
    void shouldHandleRuntimeException() {
        WebExceptionAdvice advice = new WebExceptionAdvice();
        RuntimeException ex = new RuntimeException("test error");

        Result result = advice.handleRuntimeException(ex);

        assertFalse(result.getSuccess());
        assertEquals("服务器异常", result.getErrorMsg());
    }
}
