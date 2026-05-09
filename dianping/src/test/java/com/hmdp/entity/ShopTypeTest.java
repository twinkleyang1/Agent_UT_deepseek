package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class ShopTypeTest {

    @Test
    void shouldSetAndGetBasicFields() {
        ShopType st = new ShopType();
        st.setId(1L);
        st.setName("Food");
        st.setIcon("food.png");
        st.setSort(1);

        assertEquals(1L, st.getId());
        assertEquals("Food", st.getName());
        assertEquals("food.png", st.getIcon());
        assertEquals(1, st.getSort());
    }

    @Test
    void shouldSetAndGetTimestamps() {
        ShopType st = new ShopType();
        LocalDateTime now = LocalDateTime.now();
        st.setCreateTime(now);
        st.setUpdateTime(now);

        assertEquals(now, st.getCreateTime());
        assertEquals(now, st.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        ShopType st = new ShopType()
                .setId(1L)
                .setName("Food")
                .setSort(1);

        assertEquals(1L, st.getId());
        assertEquals("Food", st.getName());
        assertEquals(1, st.getSort());
    }
}
