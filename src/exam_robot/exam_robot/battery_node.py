#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import time

class BatteryNode(Node):
    def __init__(self):
        super().__init__('battery_node')
        
        # Создаем издателя для топика /battery_level с типом Float32
        self.publisher_ = self.create_publisher(Float32, '/battery_level', 10)
        
        # Инициализируем уровень заряда (Начальный заряд: 100.0%)
        self.battery_level = 100.0
        
        # Переменная для хранения предыдущего целого значения процента (для логирования)
        # Логируем только при смене десятков процентов (100 -> 90, 90 -> 80 и т.д.)
        self.last_logged_tens = 10  # 100% соответствует десятку 10 (100/10)
        
        # Создаем таймер для публикации с частотой 1 Hz
        self.timer = self.create_timer(1.0, self.timer_callback)
        
        self.get_logger().info('Battery Node запущен. Начальный заряд: 100.0%')

    def timer_callback(self):
        # Создаем сообщение типа Float32
        msg = Float32()
        
        # Уменьшаем заряд, только если он больше 0
        if self.battery_level > 0.0:
            # Разряд: -1.0% каждую секунду
            self.battery_level -= 1.0
            
            # Гарантируем, что заряд не станет отрицательным
            if self.battery_level < 0.0:
                self.battery_level = 0.0
        
        # Присваиваем текущее значение заряда сообщению
        msg.data = self.battery_level
        
        # Публикуем сообщение в топик /battery_level
        self.publisher_.publish(msg)
        
        # --- Логирование каждые 10% ---
        # Округляем текущий уровень заряда до целого числа для проверки десятков
        current_int = int(self.battery_level)
        # Определяем, какой сейчас десяток процентов (0-10, где 10 = 100%, 0 = 0%)
        # Делим на 10, чтобы получить число десятков
        current_tens = current_int // 10
        
        # Проверяем, изменился ли десяток процентов и не логали ли мы это уже
        # Также логируем 0%, когда батарея разрядилась
        if current_tens < self.last_logged_tens or (self.battery_level == 0.0 and self.last_logged_tens != 0):
            # Обработка специального случая для 0% (current_tens = 0)
            if self.battery_level == 0.0:
                self.get_logger().warn(f'Battery: 0% (разряжена)')
                self.last_logged_tens = 0
            else:
                # Логируем уровень заряда, кратный 10
                # Умножаем current_tens на 10, чтобы получить корректное значение (90, 80, 70...)
                log_value = current_tens * 10
                # Для случая 100% current_tens = 10, log_value = 100
                if log_value == 100:
                    # Начальное состояние уже залогировано в конструкторе, но на всякий случай:
                    if self.last_logged_tens == 10:
                        pass # Уже залогировано
                    else:
                        self.get_logger().info(f'Battery: {log_value}%')
                else:
                    self.get_logger().info(f'Battery: {log_value}%')
                self.last_logged_tens = current_tens
        
        # Альтернативный простой способ логирования (если первый кажется сложным):
        # Просто проверяем, кратен ли текущий уровень заряда 10, и не логали ли мы его.
        # Этот способ проще, но может пропустить 100% в начале, если мы не логируем сразу.
        # Для простоты и надежности в условиях задачи, можно использовать этот вариант:
        #
        # current_int = int(self.battery_level)
        # if current_int % 10 == 0 and current_int != self.last_logged_int:
        #     self.get_logger().info(f'Battery: {current_int}%')
        #     self.last_logged_int = current_int

def main(args=None):
    rclpy.init(args=args)
    battery_node = BatteryNode()
    
    try:
        rclpy.spin(battery_node)
    except KeyboardInterrupt:
        pass
    finally:
        battery_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()