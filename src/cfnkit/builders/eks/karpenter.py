from troposphere import events, sqs, Ref, GetAtt

from cfnkit import helpers


def _get_karpenter_event_targets(queue: sqs.Queue):
    return [
        events.Target(Id="EksKarpenterInterruptQueueTarget", Arn=GetAtt(queue, "Arn"))
    ]


def get_interrupt_queue():
    return sqs.Queue(
        "EksKarpenterInterruptQueue",
        MessageRetentionPeriod=300,
        SqsManagedSseEnabled=True,
    )


def get_interrupt_queue_policy(queue: sqs.Queue):
    return sqs.QueuePolicy(
        "EksKarpenterInterruptQueuePolicy",
        Queues=[Ref(queue)],
        PolicyDocument={
            "Id": "EC2InterruptionPolicy",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["events.amazonaws.com", "sqs.amazonaws.com"]
                    },
                    "Action": "sqs:SendMessage",
                    "Resource": GetAtt(queue, "Arn"),
                }
            ],
        },
    )


def get_scheduled_change_rule(queue: sqs.Queue):
    return helpers.get_event_rule(
        "EksKarpenterScheduledChangeRule",
        "AWS Health Event",
        _get_karpenter_event_targets(queue),
        "aws.health",
    )


def get_spot_interruption_rule(queue: sqs.Queue):
    return helpers.get_event_rule(
        "EksKarpenterSpotInterruptionRule",
        "EC2 Spot Instance Interruption Warning",
        _get_karpenter_event_targets(queue),
    )


def get_rebalance_rule(queue: sqs.Queue):
    return helpers.get_event_rule(
        "EksKarpenterRebalanceRule",
        "EC2 Instance Rebalance Recommendation",
        _get_karpenter_event_targets(queue),
    )


def get_instance_state_rule(queue: sqs.Queue):
    return helpers.get_event_rule(
        "EksKarpenterInstanceStateChangeRule",
        "EC2 Instance State-change Notification",
        _get_karpenter_event_targets(queue),
    )
