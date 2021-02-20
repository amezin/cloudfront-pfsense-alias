#!/usr/bin/env python3

import argparse
import ipaddress
import json
import sys


def merge(addrs):
    addrs = sorted(addrs)
    if not addrs:
        return []

    merged = []

    def add_merged(addr):
        while merged:
            prev = merged[-1]
            if addr.subnet_of(prev):
                return

            addr_super = addr.supernet()
            if tuple(addr_super.subnets()) != (prev, addr):
                break

            addr = addr_super
            del merged[-1]

        merged.append(addr)

    for addr in addrs:
        add_merged(addr)

    return merged


def extract_subnets(key, json_list):
    return merge(
        ipaddress.ip_network(item[key])
        for item in json_list
        if item['service'] == 'CLOUDFRONT'
    )


def run(ip_ranges_json, output, output_v6):
    data = json.load(ip_ranges_json)

    merged_v4 = extract_subnets('ip_prefix', data['prefixes'])
    merged_v6 = extract_subnets('ipv6_prefix', data['ipv6_prefixes'])

    print('Merged:', len(merged_v4) + len(merged_v6), file=sys.stderr)
    print('Total addresses:', sum(net.num_addresses for net in merged_v4) + sum(net.num_addresses for net in merged_v6), file=sys.stderr)

    for net in merged_v4:
        print(net, file=output)

    if output_v6 is None:
        output_v6 = output

    for net in merged_v6:
        print(net, file=output_v6)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ip_ranges_json', type=argparse.FileType('r'))
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-6', '--output-v6', type=argparse.FileType('w'))
    run(**vars(parser.parse_args()))


if __name__ == '__main__':
    main()
