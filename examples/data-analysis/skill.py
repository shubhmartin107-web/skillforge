import math


def analyze(numbers: list, include_histogram: bool = False) -> dict:
    nums = [float(n) for n in numbers]
    n = len(nums)
    if n == 0:
        return {"error": "Empty list", "count": 0}

    sorted_nums = sorted(nums)
    total = sum(nums)
    mean = total / n

    if n % 2 == 1:
        median = sorted_nums[n // 2]
    else:
        median = (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2

    variance = sum((x - mean) ** 2 for x in nums) / n
    std_dev = math.sqrt(variance)

    result = {
        "count": n,
        "sum": round(total, 4),
        "mean": round(mean, 4),
        "median": round(median, 4),
        "min": round(min(nums), 4),
        "max": round(max(nums), 4),
        "std_dev": round(std_dev, 4),
    }

    if include_histogram and n > 0:
        bins = 10
        bin_width = (max(nums) - min(nums)) / bins if max(nums) > min(nums) else 1
        hist = {}
        for i in range(bins):
            lo = min(nums) + i * bin_width
            hi = lo + bin_width
            label = f"{lo:.1f}-{hi:.1f}"
            count = sum(1 for x in nums if lo <= x < hi)
            bar = "#" * count
            hist[label] = f"{bar} ({count})"
        result["histogram"] = "\n".join(f"{k}: {v}" for k, v in hist.items())

    return result
