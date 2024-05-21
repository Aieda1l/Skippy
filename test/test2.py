import math
from typing import List

class Rectangle:
    def __init__(self, left, top, right, bottom):
        self.Left = left
        self.Top = top
        self.Right = right
        self.Bottom = bottom

    def Width(self):
        return self.Right - self.Left

    def Height(self):
        return self.Bottom - self.Top

    def Center(self):
        return ((self.Left + self.Right) / 2, (self.Top + self.Bottom) / 2)


class TrackedObject:
    def __init__(self, detection, obj_id, time):
        self.Detection = detection
        self.Id = obj_id
        self.Time = time


class Detection:
    def __init__(self, bounding_box):
        self.BoundingBox = bounding_box


class TextShape:
    def __init__(self, position, text, color, size):
        self.Position = position
        self.Text = text
        self.Color = color
        self.Size = size


class HungarianTracker:
    def __init__(self):
        self.trackedObjects = []
        self.droppedObjects = []
        self.dropIds = []
        self.nextId = 1
        self.disposed = False
        self.MaximumInactiveTime = 0.25
        self.MaximumTrackingDistance = 256

    @property
    def Active(self):
        return self.trackedObjects

    @property
    def Inactive(self):
        return self.droppedObjects

    def Clear(self):
        self.trackedObjects.clear()
        self.droppedObjects.clear()
        self.dropIds.clear()
        self.nextId = 1

    def Track(self, detections, dt):
        for i in range(len(self.droppedObjects) - 1, -1, -1):
            dropped = self.droppedObjects[i]
            if dropped.Time + dt > self.MaximumInactiveTime:
                self.droppedObjects.pop(i)
            else:
                self.droppedObjects[i] = TrackedObject(dropped.Detection, dropped.Id, dropped.Time + dt)

        rows = len(self.trackedObjects) + len(self.droppedObjects)
        cols = len(detections)
        dimensions = max(rows, cols)
        costs = [[0.0] * dimensions for _ in range(dimensions)]

        for r in range(len(detections)):
            detection = detections[r]

            for c in range(len(self.trackedObjects)):
                costs[r][c] = self.GIOU(detection.BoundingBox, self.trackedObjects[c].Detection.BoundingBox)

            for c in range(len(self.droppedObjects)):
                costs[r][len(self.trackedObjects) + c] = self.GIOU(
                    detection.BoundingBox, self.droppedObjects[c].Detection.BoundingBox
                )

        assignments = self.HungarianAlgorithm.FindAssignments(costs)

        persisted_count = len(self.trackedObjects)
        maximum_distance_sq = self.MaximumTrackingDistance ** 2

        for r in range(len(detections)):
            detection = detections[r]
            detection_center = detection.BoundingBox.Center()
            c = assignments[r]

            if c < len(self.trackedObjects):
                tracked = self.trackedObjects[c]
                distance_sq = detection_center.DistanceSq(tracked.Detection.BoundingBox.Center())

                if distance_sq <= maximum_distance_sq:
                    self.trackedObjects[c] = TrackedObject(
                        detection, self.trackedObjects[c].Id, self.trackedObjects[c].Time + dt
                    )
                else:
                    self.trackedObjects.pop(c)
                    self.trackedObjects.append(TrackedObject(detection, self.nextId, 0.0))
                    self.droppedObjects.append(TrackedObject(tracked.Detection, tracked.Id, 0.0))
                    persisted_count -= 1
            elif c < rows:
                idx = rows - len(self.trackedObjects) - 1
                dropped = self.droppedObjects[idx]
                distance_sq = detection_center.DistanceSq(dropped.Detection.BoundingBox.Center())

                if distance_sq <= maximum_distance_sq:
                    self.trackedObjects.append(TrackedObject(detection, dropped.Id, 0.0))
                    self.droppedObjects.pop(idx)
                else:
                    self.trackedObjects.append(TrackedObject(detection, self.nextId, 0.0))
            else:
                self.trackedObjects.append(TrackedObject(detection, self.nextId, 0.0))

        drop_ids = []

        for r in range(len(detections), len(assignments)):
            c = assignments[r]

            if c < persisted_count:
                tracked = self.trackedObjects[c]
                drop_ids.append(tracked.Id)
                self.droppedObjects.append(TrackedObject(tracked.Detection, tracked.Id, 0.0))

        for obj_id in drop_ids:
            for i in range(persisted_count):
                if self.trackedObjects[i].Id == obj_id:
                    self.trackedObjects.pop(i)
                    persisted_count -= 1
                    break

    @staticmethod
    def GIOU(r1, r2):
        a1 = r1.Width() * r1.Height()
        a2 = r2.Width() * r2.Height()

        if a1 <= 0.0 or a2 <= 0.0:
            return 1.0

        xi1 = max(r1.Left, r2.Left)
        xi2 = min(r1.Right, r2.Right)
        yi1 = max(r1.Top, r2.Top)
        yi2 = min(r1.Bottom, r2.Bottom)
        ai = max(0.0, (xi2 - xi1) * (yi2 - yi1))

        xc1 = min(r1.Left, r2.Left)
        xc2 = max(r1.Right, r2.Right)
        yc1 = min(r1.Top, r2.Top)
        yc2 = max(r1.Bottom, r2.Bottom)
        ac = (xc2 - xc1) * (yc2 - yc1)

        au = a1 + a2 - ai
        iou = ai / au
        giou = iou - ((ac - au) / ac)

        return 1.0 - giou

    def Dispose(self):
        self.Dispose(True)

    def Dispose(self, disposing):
        if not self.disposed:
            if disposing:
                # TODO: Dispose of managed state (managed objects).
                pass

            self.disposed = True

    class HungarianAlgorithm:
        @staticmethod
        def FindAssignments(costs):
            h = len(costs)
            w = len(costs[0])

            for i in range(h):
                min_val = min(costs[i])
                for j in range(w):
                    costs[i][j] -= min_val

            masks = [[0] * w for _ in range(h)]
            rows_covered = [False] * h
            cols_covered = [False] * w

            for i in range(h):
                for j in range(w):
                    if costs[i][j] == 0 and not rows_covered[i] and not cols_covered[j]:
                        masks[i][j] = 1
                        rows_covered[i] = True
                        cols_covered[j] = True

            HungarianTracker.HungarianAlgorithm.ClearCovers(rows_covered, cols_covered, w, h)

            path = [HungarianTracker.HungarianAlgorithm.Location(0, 0)] * (w * h)
            path_start = HungarianTracker.HungarianAlgorithm.Location(0, 0)
            step = 1

            while step != -1:
                if step == 1:
                    step = HungarianTracker.HungarianAlgorithm.RunStep1(masks, cols_covered, w, h)
                elif step == 2:
                    step = HungarianTracker.HungarianAlgorithm.RunStep2(
                        costs, masks, rows_covered, cols_covered, w, h, path_start
                    )
                elif step == 3:
                    step = HungarianTracker.HungarianAlgorithm.RunStep3(masks, rows_covered, cols_covered, w, h, path, path_start)
                elif step == 4:
                    step = HungarianTracker.HungarianAlgorithm.RunStep4(costs, masks, rows_covered, cols_covered, w, h)

            agents_tasks = [0] * h

            for i in range(h):
                for j in range(w):
                    if masks[i][j] == 1:
                        agents_tasks[i] = j
                        break

            return agents_tasks

        @staticmethod
        def RunStep1(masks, cols_covered, w, h):
            for i in range(h):
                for j in range(w):
                    if masks[i][j] == 1:
                        cols_covered[j] = True

            cols_covered_count = sum(cols_covered)

            if cols_covered_count == h:
                return -1
            else:
                return 2

        @staticmethod
        def RunStep2(costs, masks, rows_covered, cols_covered, w, h, path_start):
            loc = HungarianTracker.HungarianAlgorithm.Location(0, 0)

            while True:
                loc = HungarianTracker.HungarianAlgorithm.FindZero(costs, rows_covered, cols_covered, w, h)
                if loc.Row == -1:
                    return 4
                else:
                    masks[loc.Row][loc.Column] = 2
                    star_col = HungarianTracker.HungarianAlgorithm.FindStarInRow(masks, w, loc.Row)

                    if star_col != -1:
                        rows_covered[loc.Row] = True
                        cols_covered[star_col] = False
                    else:
                        path_start = loc
                        return 3

        @staticmethod
        def RunStep3(masks, rows_covered, cols_covered, w, h, path, path_start):
            path_index = 0
            path[path_index] = path_start

            while True:
                row = HungarianTracker.HungarianAlgorithm.FindStarInColumn(masks, h, path[path_index].Column)
                if row == -1:
                    break

                path_index += 1
                path[path_index] = HungarianTracker.HungarianAlgorithm.Location(row, path[path_index - 1].Column)
                col = HungarianTracker.HungarianAlgorithm.FindPrimeInRow(masks, w, path[path_index].Row)
                path_index += 1
                path[path_index] = HungarianTracker.HungarianAlgorithm.Location(path[path_index - 1].Row, col)

            HungarianTracker.HungarianAlgorithm.ConvertPath(masks, path, path_index + 1)
            HungarianTracker.HungarianAlgorithm.ClearCovers(rows_covered, cols_covered, w, h)
            HungarianTracker.HungarianAlgorithm.ClearPrimes(masks, w, h)

            return 1

        @staticmethod
        def RunStep4(costs, masks, rows_covered, cols_covered, w, h):
            min_value = HungarianTracker.HungarianAlgorithm.FindMinimum(costs, rows_covered, cols_covered, w, h)

            for i in range(h):
                for j in range(w):
                    if rows_covered[i]:
                        costs[i][j] += min_value

                    if not cols_covered[j]:
                        costs[i][j] -= min_value

            return 2

        @staticmethod
        def ConvertPath(masks, path, path_length):
            for i in range(path_length):
                if masks[path[i].Row][path[i].Column] == 1:
                    masks[path[i].Row][path[i].Column] = 0
                elif masks[path[i].Row][path[i].Column] == 2:
                    masks[path[i].Row][path[i].Column] = 1

        @staticmethod
        def FindZero(costs, rows_covered, cols_covered, w, h):
            for i in range(h):
                for j in range(w):
                    if costs[i][j] == 0.0 and not rows_covered[i] and not cols_covered[j]:
                        return HungarianTracker.HungarianAlgorithm.Location(i, j)

            return HungarianTracker.HungarianAlgorithm.Location(-1, -1)

        @staticmethod
        def FindMinimum(costs, rows_covered, cols_covered, w, h):
            min_value = float('inf')

            for i in range(h):
                for j in range(w):
                    if not rows_covered[i] and not cols_covered[j]:
                        min_value = min(min_value, costs[i][j])

            return min_value

        @staticmethod
        def FindStarInRow(masks, w, row):
            for j in range(w):
                if masks[row][j] == 1:
                    return j

            return -1

        @staticmethod
        def FindStarInColumn(masks, h, col):
            for i in range(h):
                if masks[i][col] == 1:
                    return i

            return -1

        @staticmethod
        def FindPrimeInRow(masks, w, row):
            for j in range(w):
                if masks[row][j] == 2:
                    return j

            return -1

        @staticmethod
        def ClearCovers(rows_covered, cols_covered, w, h):
            for i in range(h):
                rows_covered[i] = False

            for j in range(w):
                cols_covered[j] = False

        @staticmethod
        def ClearPrimes(masks, w, h):
            for i in range(h):
                for j in range(w):
                    if masks[i][j] == 2:
                        masks[i][j] = 0

        class Location:
            def __init__(self, row, col):
                self.Row = row
                self.Column = col


# Example usage:
tracker = HungarianTracker()
detections = [Detection(Rectangle(0, 0, 10, 10)), Detection(Rectangle(15, 15, 25, 25))]
dt = 0.1  # Replace with your time delta
tracker.Track(detections, dt)
print(tracker.trackedObjects[0].Id)
