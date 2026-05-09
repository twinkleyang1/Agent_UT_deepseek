package com.hmdp.dto;

import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ScrollResultTest {

    @Test
    void shouldSetAndGetList() {
        ScrollResult result = new ScrollResult();
        List<String> list = List.of("a", "b");
        result.setList(list);

        assertEquals(list, result.getList());
    }

    @Test
    void shouldSetAndGetMinTime() {
        ScrollResult result = new ScrollResult();
        result.setMinTime(1000L);

        assertEquals(1000L, result.getMinTime());
    }

    @Test
    void shouldSetAndGetOffset() {
        ScrollResult result = new ScrollResult();
        result.setOffset(5);

        assertEquals(5, result.getOffset());
    }

    @Test
    void shouldSetAllFields() {
        ScrollResult result = new ScrollResult();
        List<Integer> list = List.of(1, 2, 3);
        result.setList(list);
        result.setMinTime(500L);
        result.setOffset(0);

        assertEquals(list, result.getList());
        assertEquals(500L, result.getMinTime());
        assertEquals(0, result.getOffset());
    }
}
