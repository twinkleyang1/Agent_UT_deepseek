package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class ShopTest {

    @Test
    void shouldSetAndGetBasicFields() {
        Shop shop = new Shop();
        shop.setId(1L);
        shop.setName("Test Shop");
        shop.setTypeId(10L);
        shop.setAddress("Shanghai");
        shop.setAvgPrice(100L);
        shop.setSold(50);
        shop.setComments(20);
        shop.setScore(45);
        shop.setOpenHours("10:00-22:00");

        assertEquals(1L, shop.getId());
        assertEquals("Test Shop", shop.getName());
        assertEquals(10L, shop.getTypeId());
        assertEquals("Shanghai", shop.getAddress());
        assertEquals(100L, shop.getAvgPrice());
        assertEquals(50, shop.getSold());
        assertEquals(20, shop.getComments());
        assertEquals(45, shop.getScore());
        assertEquals("10:00-22:00", shop.getOpenHours());
    }

    @Test
    void shouldSetAndGetCoordinates() {
        Shop shop = new Shop();
        shop.setX(121.4737);
        shop.setY(31.2304);

        assertEquals(121.4737, shop.getX());
        assertEquals(31.2304, shop.getY());
    }

    @Test
    void shouldSetAndGetDistance() {
        Shop shop = new Shop();
        shop.setDistance(1.5);

        assertEquals(1.5, shop.getDistance());
    }

    @Test
    void shouldSetAndGetImages() {
        Shop shop = new Shop();
        shop.setImages("img1.jpg,img2.jpg");

        assertEquals("img1.jpg,img2.jpg", shop.getImages());
    }

    @Test
    void shouldSetAndGetArea() {
        Shop shop = new Shop();
        shop.setArea("Lujiazui");

        assertEquals("Lujiazui", shop.getArea());
    }

    @Test
    void shouldSetAndGetTimestamps() {
        Shop shop = new Shop();
        LocalDateTime now = LocalDateTime.now();
        shop.setCreateTime(now);
        shop.setUpdateTime(now);

        assertEquals(now, shop.getCreateTime());
        assertEquals(now, shop.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        Shop shop = new Shop()
                .setId(1L)
                .setName("Test")
                .setTypeId(10L);

        assertEquals(1L, shop.getId());
        assertEquals("Test", shop.getName());
        assertEquals(10L, shop.getTypeId());
    }
}
