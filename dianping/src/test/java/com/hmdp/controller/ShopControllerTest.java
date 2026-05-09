package com.hmdp.controller;

import com.hmdp.dto.Result;
import com.hmdp.entity.Shop;
import com.hmdp.service.IShopService;
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
class ShopControllerTest {

    @Mock private IShopService shopService;
    @InjectMocks private ShopController controller;

    @Test
    void shouldQueryShopById() throws InterruptedException {
        Shop shop = new Shop().setId(1L).setName("Test");
        when(shopService.queryById(1L)).thenReturn(Result.ok(shop));

        Result result = controller.queryShopById(1L);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldSaveShop() {
        Shop shop = new Shop().setId(1L).setName("New Shop");
        when(shopService.save(shop)).thenReturn(true);

        Result result = controller.saveShop(shop);

        assertTrue(result.getSuccess());
        assertEquals(1L, result.getData());
        verify(shopService).save(shop);
    }

    @Test
    void shouldUpdateShop() {
        Shop shop = new Shop().setId(1L).setName("Updated");
        when(shopService.update(shop)).thenReturn(Result.ok());

        Result result = controller.updateShop(shop);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldQueryShopByType() {
        when(shopService.queryShopByType(5, 1, null, null)).thenReturn(Result.ok());

        Result result = controller.queryShopByType(5, 1, null, null);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldQueryShopByTypeWithCoords() {
        when(shopService.queryShopByType(5, 1, 31.2, 121.4)).thenReturn(Result.ok());

        Result result = controller.queryShopByType(5, 1, 31.2, 121.4);

        assertTrue(result.getSuccess());
    }
}
