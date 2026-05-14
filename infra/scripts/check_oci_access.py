from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OCI access for OCI Architecture Studio.")
    parser.add_argument("--profile", default="DEFAULT", help="OCI CLI profile for local validation.")
    parser.add_argument("--compartment-id", help="Compartment OCID to list buckets/log groups in.")
    parser.add_argument("--bucket-name", help="Object Storage bucket name to verify.")
    parser.add_argument("--secret-id", help="Vault secret OCID to verify read access.")
    parser.add_argument("--log-group-id", help="Logging log group OCID to verify.")
    parser.add_argument("--alarm-id", help="Monitoring alarm OCID to verify read access.")
    parser.add_argument("--event-rule-id", help="Events rule OCID to verify read access.")
    return parser.parse_args()


def main() -> int:
    try:
        import oci
    except ImportError:
        print("FAIL OCI SDK is not installed. Install with `pip install oci`.", file=sys.stderr)
        return 1

    args = parse_args()
    config = oci.config.from_file(profile_name=args.profile)

    object_storage = oci.object_storage.ObjectStorageClient(config)
    namespace = object_storage.get_namespace().data
    print(f"PASS object storage namespace: {namespace}")

    if args.compartment_id:
        buckets = object_storage.list_buckets(namespace, args.compartment_id).data
        print(f"PASS bucket list: {len(buckets)} bucket(s) visible")
        if args.bucket_name:
            matching = [bucket for bucket in buckets if bucket.name == args.bucket_name]
            assert matching, f"bucket not found: {args.bucket_name}"
            print(f"PASS bucket found: {args.bucket_name}")

    if args.secret_id:
        secrets = oci.secrets.SecretsClient(config)
        bundle = secrets.get_secret_bundle(args.secret_id).data
        assert bundle.secret_id == args.secret_id
        print("PASS secret bundle readable")

    if args.log_group_id:
        logging = oci.logging.LoggingManagementClient(config)
        log_group = logging.get_log_group(args.log_group_id).data
        assert log_group.id == args.log_group_id
        print(f"PASS log group readable: {log_group.display_name}")

    if args.alarm_id:
        monitoring = oci.monitoring.MonitoringClient(config)
        alarm = monitoring.get_alarm(args.alarm_id).data
        assert alarm.id == args.alarm_id
        print(f"PASS monitoring alarm readable: {alarm.display_name}")

    if args.event_rule_id:
        events = oci.events.EventsClient(config)
        rule = events.get_rule(args.event_rule_id).data
        assert rule.id == args.event_rule_id
        print(f"PASS events rule readable: {rule.display_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
