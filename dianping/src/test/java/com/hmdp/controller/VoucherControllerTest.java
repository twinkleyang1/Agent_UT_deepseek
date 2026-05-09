package com.hmdp.controller;

import com.hmdp.dto.Result;
import com.hmdp.entity.Voucher;
import com.hmdp.service.IVoucherService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class VoucherControllerTest {

    @Mock private IVoucherService voucherService;
    @InjectMocks private VoucherController controller;

    @Test
    void shouldAddVoucher() {
        Voucher v = new Voucher().setId(1L);
        doNothing().when(voucherService).addSeckillVoucher(v);

        Result result = controller.addVoucher(v);

        assertTrue(result.getSuccess());
        assertEquals(1L, result.getData());
        verify(voucherService).addSeckillVoucher(v);
    }

    @Test
    void shouldAddSeckillVoucher() {
        Voucher v = new Voucher().setId(2L);
        doNothing().when(voucherService).addSeckillVoucher(v);

        Result result = controller.addSeckillVoucher(v);

        assertTrue(result.getSuccess());
        assertEquals(2L, result.getData());
        verify(voucherService).addSeckillVoucher(v);
    }

    @Test
    void shouldQueryVoucherOfShop() {
        when(voucherService.queryVoucherOfShop(10L)).thenReturn(Result.ok(List.of()));

        Result result = controller.queryVoucherOfShop(10L);

        assertTrue(result.getSuccess());
    }
}
