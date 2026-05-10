package com.hmdp.config;

import org.junit.jupiter.api.Test;
import org.springframework.amqp.core.Queue;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class QueueConfigTest {

    @Test
    void shouldReturnQueueWhenQueueA() {
        // Arrange
        QueueConfig config = new QueueConfig();

        // Act
        Queue queue = config.queueA();

        // Assert
        assertNotNull(queue);
        assertEquals("QA", queue.getName());
    }
}
