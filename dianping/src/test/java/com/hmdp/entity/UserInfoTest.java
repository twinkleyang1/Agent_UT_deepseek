package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDate;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class UserInfoTest {

    @Test
    void shouldSetAndGetFields() {
        UserInfo ui = new UserInfo();
        ui.setUserId(1L);
        ui.setCity("Shanghai");
        ui.setIntroduce("Hello world");
        ui.setFans(100);
        ui.setFollowee(50);
        ui.setGender(true);
        ui.setBirthday(LocalDate.of(1990, 1, 1));
        ui.setCredits(500);
        ui.setLevel(true);
        LocalDateTime now = LocalDateTime.now();
        ui.setCreateTime(now);
        ui.setUpdateTime(now);

        assertEquals(1L, ui.getUserId());
        assertEquals("Shanghai", ui.getCity());
        assertEquals("Hello world", ui.getIntroduce());
        assertEquals(100, ui.getFans());
        assertEquals(50, ui.getFollowee());
        assertTrue(ui.getGender());
        assertEquals(LocalDate.of(1990, 1, 1), ui.getBirthday());
        assertEquals(500, ui.getCredits());
        assertTrue(ui.getLevel());
        assertEquals(now, ui.getCreateTime());
        assertEquals(now, ui.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        UserInfo ui = new UserInfo()
                .setUserId(1L)
                .setCity("Beijing")
                .setFans(200);

        assertEquals(1L, ui.getUserId());
        assertEquals("Beijing", ui.getCity());
        assertEquals(200, ui.getFans());
    }
}
