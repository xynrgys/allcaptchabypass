if not grid:
    return 0

rows, cols = len(grid), len(grid[0])
visiteed = set()
islands = 0

def bfs(r, c):
    q = deque()
    visiteed.add((r, c))
    q.append((r, c))
    while q:
        row, col = q.popleft()
        directions = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if (r in range(rows) and
                c in range(cols) and
                grid[r][c] == "1" and
                (r, c) not in visiteed):
                q.append((r, c))
                visiteed.add((r, c))

for r in range(rows):
    for c in range(cols):
        if grid[r][c] == "1" and (r, c) not in visiteed:
            islands += 1
            bfs(r, c)
            
return islands


if not grid:
    return 0

islands = 0

rows, cols = len(grid), len(grid[0])

def mark_visited(i, j):
    if i < 0 or i >= rows or j < 0 or j >= cols or grid[i][j] == '0':
        return
    grid[i][j] = '0'
    mark_visited(i + 1, j)
    mark_visited(i - 1, j)

slow = head
        fast = head.next

        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next

        second = slow.next
        prev = slow.next = None
        while second:
            temp = second.next
            second.next = prev
            prev = second
            second = temp

        first, second = head, prev
        while second:
            temp1, temp2 = first.next, second.next
            first.next = second
            second.next = temp1
            first, second = temp1, temp2
            
res = [root.val]

def dfs(root):
    if not root:
        return 0
    
    leftMax = dfs(root.left)
    rightMax = dfs(root.right)
    leftMax = max(leftMax, 0)
    rightMax = max(rightMax, 0)
        
    res[0] = max(res[0], root.val + leftMax + rightMax)
    
    return root.val + max(leftMax, rightMax)

dfs(root)
return res[0]



def serialize:
    res = []
    
    def dfs(node):
        if not node:
            res.append("N")
            return
        res.append(str(node.val))
        dfs(node.left)
        dfs(node.right)
        
    dfs(root)
    return ",".join(res)

def deserialize:
    vals = data.split(",")
    self.i
    
    def dfs():
        if vals[self.i] == "N":
            self.i += 1
            return None
        node = TreeNode(int(vals[self.i]))
        self.i += 1
        node.left = dfs()
        node.right = dfs()
        return node
    return dfs()


if not height:
    return 0

l, r = 0, len(height) - 1
leftMax, rightMax = height[l], height[r]
res = 0

while l < r:
    if leftMax < rightMax:
        l += 1
        leftMax = max(leftMax, height[l])
        res += leftMax - height[l]
    else:
        r -= 1
        rightMax = max(rightMax, height[r])
        res += rightMax - height[r]
        
return res


maxArea = 0
strack = [] 

for i, h in enumerate(heights):
    start = i
    while stack and stack[-1][1] > h:
        index, height = stack.pop()
        maxArea = max(maxArea, height * (i - index))
        start = index
    stack.append((start, h))
    
    for i, h in stack:
        maxArea = max(maxArea, h * (len(heights) - i))
    return maxArea



if t == "":
    return ""

countT, window = {}, {}

for c in t:
    countT[c] = 1 + countT.get(c, 0)

have, need = 0, len(countT)
res, resLen = [-1, -1], float("infinity")
l = 0

for r in range(len(s)):
    c = s[r]
    window[c] = 1 + window.get(c, 0)
    
    if c in countT and window[c] == countT[c]:
        have += 1
        
    while have == need:
        if (r - l + 1) < resLen:
            res = [l, r]
            resLen = (r - 1 + 1)
        #pop from the left of our window
        window[s[l]] -= 1
        if s[l] in countT and window[s[l]] < countT[s[l]]:
            have -= 1
        l += 1
        
    l, r = res
    return s[l:r+1] if resLen != float("infinity") else ""



output = []
l = r = 0
q = deque() # indeces

while r < len(nums):
    while q and nums[r] > nums[q[-1]]:
        q.pop()
    q.append(r)
    
    if l > q[0]:
        q.popleft()
        
    if (r+1) >= k:
        output.append(nnums[q[0]])
        l += 1
    r += 1
    
return output




