package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class VoucherTest {

    @Test
    void shouldSetAndGetBasicFields() {
        Voucher v = new Voucher();
        v.setId(1L);
        v.setShopId(10L);
        v.setTitle("50% off");
        v.setSubTitle("Limited time offer");
        v.setRules("Min spend 100");
        v.setPayValue(5000L);
        v.setActualValue(10000L);
        v.setType(1);
        v.setStatus(1);

        assertEquals(1L, v.getId());
        assertEquals(10L, v.getShopId());
        assertEquals("50% off", v.getTitle());
        assertEquals("Limited time offer", v.getSubTitle());
        assertEquals("Min spend 100", v.getRules());
        assertEquals(5000L, v.getPayValue());
        assertEquals(10000L, v.getActualValue());
        assertEquals(1, v.getType());
        assertEquals(1, v.getStatus());
    }

    @Test
    void shouldSetAndGetTableFieldExcluded() {
        Voucher v = new Voucher();
        v.setStock(100);
        v.setBeginTime(LocalDateTime.now());
        v.setEndTime(LocalDateTime.now().plusDays(7));

        assertEquals(100, v.getStock());
        assertNotNull(v.getBeginTime());
        assertNotNull(v.getEndTime());
    }

    @Test
    void shouldSetAndGetTimestamps() {
        Voucher v = new Voucher();
        LocalDateTime now = LocalDateTime.now();
        v.setCreateTime(now);
        v.setUpdateTime(now);

        assertEquals(now, v.getCreateTime());
        assertEquals(now, v.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        Voucher v = new Voucher()
                .setId(1L)
                .setShopId(10L)
                .setTitle("Test");

        assertEquals(1L, v.getId());
        assertEquals(10L, v.getShopId());
        assertEquals("Test", v.getTitle());
    }
}
