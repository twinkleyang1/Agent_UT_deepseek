package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class FollowTest {

    @Test
    void shouldSetAndGetFields() {
        Follow f = new Follow();
        f.setId(1L);
        f.setUserId(100L);
        f.setFollowUserId(200L);
        LocalDateTime now = LocalDateTime.now();
        f.setCreateTime(now);

        assertEquals(1L, f.getId());
        assertEquals(100L, f.getUserId());
        assertEquals(200L, f.getFollowUserId());
        assertEquals(now, f.getCreateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        Follow f = new Follow()
                .setId(1L)
                .setUserId(100L)
                .setFollowUserId(200L);

        assertEquals(1L, f.getId());
        assertEquals(100L, f.getUserId());
        assertEquals(200L, f.getFollowUserId());
    }
}
