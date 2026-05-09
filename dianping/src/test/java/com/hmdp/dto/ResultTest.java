package com.hmdp.dto;

import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ResultTest {

    @Test
    void shouldReturnSuccessResultWhenOk() {
        Result result = Result.ok();

        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertNull(result.getErrorMsg());
        assertNull(result.getData());
        assertNull(result.getTotal());
    }

    @Test
    void shouldReturnSuccessWithDataWhenOkWithData() {
        String data = "test-data";

        Result result = Result.ok(data);

        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertEquals("test-data", result.getData());
    }

    @Test
    void shouldReturnSuccessWithListAndTotalWhenOkWithList() {
        List<String> list = List.of("a", "b", "c");

        Result result = Result.ok(list, 3L);

        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertEquals(list, result.getData());
        assertEquals(3L, result.getTotal());
    }

    @Test
    void shouldReturnFailResultWhenFail() {
        Result result = Result.fail("error occurred");

        assertNotNull(result);
        assertFalse(result.getSuccess());
        assertEquals("error occurred", result.getErrorMsg());
        assertNull(result.getData());
    }

    @Test
    void shouldReturnFailResultWhenFailWithNullMessage() {
        Result result = Result.fail(null);

        assertNotNull(result);
        assertFalse(result.getSuccess());
        assertNull(result.getErrorMsg());
    }
}
