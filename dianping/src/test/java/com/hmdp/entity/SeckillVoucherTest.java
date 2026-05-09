package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class SeckillVoucherTest {

    @Test
    void shouldSetAndGetFields() {
        SeckillVoucher sv = new SeckillVoucher();
        sv.setVoucherId(10L);
        sv.setStock(100);
        LocalDateTime now = LocalDateTime.now();
        sv.setCreateTime(now);
        sv.setBeginTime(now);
        sv.setEndTime(now.plusDays(1));
        sv.setUpdateTime(now);

        assertEquals(10L, sv.getVoucherId());
        assertEquals(100, sv.getStock());
        assertEquals(now, sv.getCreateTime());
        assertEquals(now, sv.getBeginTime());
        assertEquals(now.plusDays(1), sv.getEndTime());
        assertEquals(now, sv.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        SeckillVoucher sv = new SeckillVoucher()
                .setVoucherId(10L)
                .setStock(50);

        assertEquals(10L, sv.getVoucherId());
        assertEquals(50, sv.getStock());
    }
}
