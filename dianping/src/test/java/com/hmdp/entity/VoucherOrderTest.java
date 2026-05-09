package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class VoucherOrderTest {

    @Test
    void shouldSetAndGetBasicFields() {
        VoucherOrder vo = new VoucherOrder();
        vo.setId(1L);
        vo.setUserId(100L);
        vo.setVoucherId(10L);
        vo.setPayType(1);
        vo.setStatus(2);

        assertEquals(1L, vo.getId());
        assertEquals(100L, vo.getUserId());
        assertEquals(10L, vo.getVoucherId());
        assertEquals(1, vo.getPayType());
        assertEquals(2, vo.getStatus());
    }

    @Test
    void shouldSetAndGetTimestamps() {
        VoucherOrder vo = new VoucherOrder();
        LocalDateTime now = LocalDateTime.now();
        vo.setCreateTime(now);
        vo.setPayTime(now);
        vo.setUseTime(now);
        vo.setRefundTime(now);
        vo.setUpdateTime(now);

        assertEquals(now, vo.getCreateTime());
        assertEquals(now, vo.getPayTime());
        assertEquals(now, vo.getUseTime());
        assertEquals(now, vo.getRefundTime());
        assertEquals(now, vo.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        VoucherOrder vo = new VoucherOrder()
                .setId(1L)
                .setUserId(100L)
                .setStatus(1);

        assertEquals(1L, vo.getId());
        assertEquals(100L, vo.getUserId());
        assertEquals(1, vo.getStatus());
    }
}
