# Requirement Document: Private Set Intersection using Diffie-Hellman
1. 簡介與目標 (Introduction & Goal)

本文件旨在定義一個使用 Diffie-Hellman 原理實現的隱私集合交集 (Private Set Intersection, PSI) 協議的功能需求。此協議將在 project 專案的客戶端 (Client A 和 Client B) 上實現，專案中的ClientA/與ClientB是用來模擬在兩台不同電腦上執行的客戶端，除了儲存的資料以外，程式碼的部分應該要相同，因此程式的邏輯需要讓ClientA/與ClientB/與Server/即使在三台不同電腦上也可以正常運作。協議的目標是讓兩個客戶端能夠找出他們各自 Excel 資料集之間的交集記錄，並安全地合併與這些交集記錄相關的原始附加數據，同時最大程度地保護非交集數據的隱私。數據交換將利用 IPFS 進行。這項功能的呼叫可以讓Client在自身UserInterFace上輸入指令，從UserSession呼叫Client端的程式。

2. 參與者 (Actors)

Client A: 持有數據集 A (rawA) 和私鑰 a 的客戶端。
Client B: 持有數據集 B (rawB) 和私鑰 b 的客戶端。

3. 輸入 (Inputs)

對於每個客戶端 (A 和 B)：

原始數據文件路徑 (Raw Data File Path): 指向包含其數據的 Excel 文件 (例如 Test_Data/test_data_1.xlsx)。
標識符欄位名稱 (Identifier Column Names): 需要用於匹配的欄位名稱列表 (指定為['s_id', 'p_id', 's_sex'])。
附加數據欄位名稱 (Associated Data Column Names): 需要在找到交集後從對方獲取的欄位名稱列表 (例如 ['county', 'region']等其他名稱)。
私鑰 (Private Key): 客戶端自身的私鑰 (整數 a 或 b)。
共享質數 (Shared Prime p): 一個預先約定好的、足夠大的質數 (整數 p)，供雙方進行模冪運算。
關於private key,prime,hash可以參考encrypt.py
Excel 文件格式: 輸入的 Excel 文件應包含明確的標頭行 (Header)，對應指定的欄位名稱。
4. 核心組件/功能 (Core Components/Functions)

需要實現以下核心功能：

Excel 讀取/解析: 使用 pandas 讀取 Excel 文件到 DataFrame。
標識符哈希: 將指定的標識符欄位的值（按順序）合併成字串，使用 SHA-256 哈希，並將結果轉換為整數 (h_A / h_B)。
模冪運算: 高效計算 pow(base, exponent, modulus)。
IPFS 上傳: 將指定文件上傳到 IPFS 並返回其 CID。
IPFS 下載: 根據 CID 從 IPFS 下載指定文件。
關於IPFS上傳與下載，請參考Server/UserSession.py與UserInterFace.py。
數據比較/匹配: 比較兩個數值列表，找出共同的值。
數據提取: 根據匹配的 Hashed ID，從原始 DataFrame 中提取對應的原始附加數據欄位。
數據合併: 使用 pandas 將兩個 DataFrame 根據 Hashed ID 進行合併 (join)。
Excel 寫入: 將最終結果 DataFrame 寫入到 Excel 文件。

5. 協議步驟 (Protocol Steps)

術語定義:

rawA, rawB: 原始 DataFrame。
h_A, h_B: 記錄的 Hashed Identifier (SHA256(concat(id_cols)) -> int)。
a, b: A 和 B 的私鑰。
p: 共享質數。
c_A = h_A^a mod p, c_B = h_B^b mod p: 第一輪計算的加密值。
k_A = c_B^a mod p = h_B^{ab} mod p, k_B = c_A^b mod p = h_A^{ab} mod p: 第二輪計算的加密值（用於匹配）。
associated_data_A, associated_data_B: 原始數據中需要交換的附加數據欄位。
步驟 1: 計算並交換盲化 Hashed ID (c_A, c_B)

A: 對 rawA 中的每一行計算 h_A，然後計算 c_A = h_A^a mod p。將所有 c_A 值保存到臨時文件 (例如 c_A.xlsx 或 c_A.txt)。將此文件上傳到 IPFS，獲得 cid_cA。
B: 對 rawB 中的每一行計算 h_B，然後計算 c_B = h_B^b mod p。將所有 c_B 值保存到臨時文件 (例如 c_B.xlsx 或 c_B.txt)。將此文件上傳到 IPFS，獲得 cid_cB。
交換: A 和 B 需要某種方式交換 cid_cA 和 cid_cB（可以通過伺服器、手動或其他帶外方式）。
步驟 2: 計算雙重盲化 Hashed ID (k_A, k_B)

A: 使用 cid_cB 從 IPFS 下載 c_B 列表。對列表中的每個 c_B 值，計算 k_A = c_B^a mod p。將所有 k_A 值保存到臨時文件 (例如 k_A.xlsx 或 k_A.txt)。
B: 使用 cid_cA 從 IPFS 下載 c_A 列表。對列表中的每個 c_A 值，計算 k_B = c_A^b mod p。將所有 k_B 值保存到臨時文件 (例如 k_B.xlsx 或 k_B.txt)。
(內部映射): A 需要維護一個從原始記錄 (或 h_A) 到計算出的 k_A 的映射關係。B 同理維護 h_B 到 k_B 的映射。這對於後續匹配後提取正確數據至關重要。
步驟 3: 交換雙重盲化 Hashed ID (k_A, k_B)

A: 將包含 k_A 列表的文件 (k_A.xlsx) 上傳到 IPFS，獲得 cid_kA。
B: 將包含 k_B 列表的文件 (k_B.xlsx) 上傳到 IPFS，獲得 cid_kB。
交換: A 和 B 交換 cid_kA 和 cid_kB。
步驟 4: 識別交集並準備匹配數據 (matchA, matchB)

A: 從 IPFS 下載 k_B 列表。找出同時存在於自己計算的 k_A 列表和下載的 k_B 列表中的值。
對於每個匹配的值 v，A 使用步驟 2 中維護的映射關係，找到與 v 對應的原始 Hashed ID (h_A)。
A 從 rawA 中提取與該 h_A 對應行的原始附加數據欄位 (associated_data_A)。
A 創建一個包含兩列的 DataFrame matchA：一列是交集記錄的 h_A，另一列（或多列）是對應的 associated_data_A。將 matchA 保存到文件 (例如 matchA.xlsx)。
B: 執行對稱操作，比較自己的 k_B 和下載的 k_A，生成 matchB.xlsx，包含交集記錄的 h_B 和 associated_data_B。
步驟 5: 交換匹配數據 (matchA, matchB)

A: 上傳 matchA.xlsx 到 IPFS，獲得 cid_matchA。
B: 上傳 matchB.xlsx 到 IPFS，獲得 cid_matchB。
交換: A 和 B 交換 cid_matchA 和 cid_matchB。
步驟 6: 最終數據合併

A: 從 IPFS 下載 matchB.xlsx。使用 pandas 將自己的 matchA DataFrame 和下載的 matchB DataFrame 進行合併 (inner join)，連接鍵 (key) 為 h_A (來自 matchA) 和 h_B (來自 matchB)。
B: 執行對稱操作。
6. 輸出 (Output)

一個 Excel 文件，其中包含：
交集記錄的 Hashed ID (h_A/h_B)。
與交集記錄對應的 Client A 的原始附加數據欄位 (associated_data_A)。
與交集記錄對應的 Client B 的原始附加數據欄位 (associated_data_B)。

接著向Client傳送message提示取得交集成功

6. 非功能性需求 (Non-Functional Requirements)

易用性: 提供簡單的命令行接口 (CLI) 來啟動 PSI 流程，接收必要的輸入參數，可以新增UserInterFace.py與UserSession的option。
錯誤處理: 對文件讀寫、IPFS 操作、網絡通信（如果涉及）和計算過程中的潛在錯誤進行處理和報告。
性能: 對於大型數據集，模冪運算和數據處理可能需要優化。