from unittest import TestCase

from bmnclient.utils.string import StringUtils

STRING_TO_SNAKE_CASE_LIST = (
    ("", ""),
    ("A", "a"),
    ("a", "a"),
    ("_A_", "_a_"),
    ("_", "_"),
    ("__", "__"),
    ("HelloWorld", "hello_world"),
    ("helloWorld", "hello_world"),
    ("hello_world", "hello_world"),
    ("hello_World", "hello_world"),
    ("__HelloWorld", "__hello_world"),
    ("__HelloWorld__", "__hello_world__"),
    ("__helloWorld__", "__hello_world__"),
    ("__Hello____World__", "__hello_world__"),
    ("He_l_lo____World__", "he_l_lo_world__"),
    ("_He__L__lo____World_", "_he_l_lo_world_"),
    ("HELLOWORLD", "h_e_l_l_o_w_o_r_l_d"),  # noqa
)

STRING_TO_CAMEL_CASE_LIST = (
    ("", ""),
    ("A", "a"),
    ("a", "a"),
    ("_A_", "_a_"),
    ("_A_a_", "_aA_"),
    ("_", "_"),
    ("__", "__"),
    ("helloworld", "helloworld"),  # noqa
    ("hello_world", "helloWorld"),
    ("__hello_world__", "__helloWorld__"),
    ("__hello_World", "__helloWorld"),
    ("hello_WorlD_", "helloWorld_"),  # noqa
    ("h_e_l_l_o_w_o_r_l_d", "hELLOWORLD"), # noqa
)


class TestStringUtils(TestCase):
    def test_case(self) -> None:
        for camel, snake in STRING_TO_SNAKE_CASE_LIST:
            self.assertEqual(
                snake,
                StringUtils.toSnakeCase(camel))
        for snake, camel in STRING_TO_CAMEL_CASE_LIST:
            self.assertEqual(
                camel,
                StringUtils.toCamelCase(snake))
