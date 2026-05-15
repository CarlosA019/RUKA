import argparse

import dynamixel_sdk

from ruka_hand.utils.constants import USB_PORTS
from ruka_hand.utils.dynamixel_util import BAUDRATE, COMM_SUCCESS, PROTOCOL_VERSION


def parse_id_range(value: str) -> list[int]:
    if "-" in value:
        start, end = value.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(part) for part in value.split(",") if part]


def main():
    parser = argparse.ArgumentParser(
        description="Ping Dynamixel IDs without enabling torque or moving motors."
    )
    parser.add_argument(
        "-ht",
        "--hand_type",
        choices=USB_PORTS.keys(),
        default="right",
        help="Hand port to use from ruka_hand.utils.constants.USB_PORTS.",
    )
    parser.add_argument("--port", default=None, help="Override serial port.")
    parser.add_argument("--baud", type=int, default=BAUDRATE)
    parser.add_argument("--ids", default="0-20", help="ID range or comma list, e.g. 1-11.")
    args = parser.parse_args()

    port = args.port or USB_PORTS[args.hand_type]
    ids = parse_id_range(args.ids)

    port_handler = dynamixel_sdk.PortHandler(port)
    packet_handler = dynamixel_sdk.PacketHandler(PROTOCOL_VERSION)

    print(f"Opening {port} at {args.baud} baud")
    if not port_handler.openPort():
        raise SystemExit(f"Failed to open {port}")
    try:
        if not port_handler.setBaudRate(args.baud):
            raise SystemExit(f"Failed to set baudrate {args.baud}")

        found = []
        missing = []
        for motor_id in ids:
            model_number, comm_result, dxl_error = packet_handler.ping(
                port_handler, motor_id
            )
            if comm_result == COMM_SUCCESS and dxl_error == 0:
                found.append(motor_id)
                print(f"ID {motor_id:>3}: OK model={model_number}")
            else:
                missing.append(motor_id)
                result = packet_handler.getTxRxResult(comm_result)
                error = packet_handler.getRxPacketError(dxl_error) if dxl_error else ""
                print(f"ID {motor_id:>3}: no response ({result}{' ' + error if error else ''})")

        print()
        print(f"Found IDs: {found}")
        print(f"Missing IDs: {missing}")
    finally:
        port_handler.closePort()


if __name__ == "__main__":
    main()
