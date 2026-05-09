package com.hmdp.controller;

import com.hmdp.dto.Result;
import com.hmdp.service.IShopTypeService;
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
class ShopTypeControllerTest {

    @Mock private IShopTypeService typeService;
    @InjectMocks private ShopTypeController controller;

    @Test
    void shouldQueryTypeList() {
        when(typeService.querySort()).thenReturn(Result.ok());

        Result result = controller.queryTypeList();

        assertTrue(result.getSuccess());
        verify(typeService).querySort();
    }
}
