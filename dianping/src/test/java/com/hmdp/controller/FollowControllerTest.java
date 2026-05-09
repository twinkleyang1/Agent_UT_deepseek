package com.hmdp.controller;

import com.hmdp.dto.Result;
import com.hmdp.service.IFollowService;
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
class FollowControllerTest {

    @Mock private IFollowService followService;
    @InjectMocks private FollowController controller;

    @Test
    void shouldFollow() {
        when(followService.follow(2L, true)).thenReturn(Result.ok());

        Result result = controller.follow(2L, true);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldUnfollow() {
        when(followService.follow(2L, false)).thenReturn(Result.ok());

        Result result = controller.follow(2L, false);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldCheckIsFollow() {
        when(followService.isFollow(2L)).thenReturn(Result.ok(true));

        Result result = controller.follow(2L);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldFollowCommons() {
        when(followService.followCommons(5L)).thenReturn(Result.ok());

        Result result = controller.followCommons(5L);

        assertTrue(result.getSuccess());
    }
}
