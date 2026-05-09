package com.hmdp.controller;

import com.hmdp.dto.Result;
import com.hmdp.service.IVoucherOrderService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class VoucherOrderControllerTest {

    @Mock private IVoucherOrderService voucherOrderService;
    @InjectMocks private VoucherOrderController controller;

    @Test
    void shouldSeckillVoucher() {
        when(voucherOrderService.seckillVoucher(10L)).thenReturn(Result.ok(100L));

        Result result = controller.seckillVoucher(10L);

        assertTrue(result.getSuccess());
        assertEquals(100L, result.getData());
    }
}
