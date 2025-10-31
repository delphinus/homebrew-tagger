# Branch Protection の設定方法

PR のマージ前にテストとlintを必須にするため、以下の手順でブランチ保護を設定してください。

## 設定手順

1. GitHub リポジトリページで **Settings** タブを開く
2. 左サイドバーから **Branches** を選択
3. **Branch protection rules** セクションで **Add rule** をクリック
4. 以下のように設定:

### Branch name pattern
```
main
```

### 必須設定項目

- ☑ **Require a pull request before merging**
  - ☑ **Require approvals**: 0 または 1 (必要に応じて)

- ☑ **Require status checks to pass before merging**
  - ☑ **Require branches to be up to date before merging**
  - **Status checks that are required:**
    - `all-checks-passed` を選択 (CI ワークフローが1回実行された後に表示されます)

- ☑ **Do not allow bypassing the above settings** (推奨)

### オプション設定

- ☑ **Require conversation resolution before merging** (推奨)
- ☑ **Include administrators** (管理者にもルールを適用する場合)

## 注意事項

- 最初の CI ワークフロー実行後、`all-checks-passed` ステータスチェックが選択可能になります
- 設定後は、すべてのチェックがパスしないと PR をマージできなくなります
- 緊急時のために管理者権限でのバイパスが必要な場合は、"Include administrators" のチェックを外してください

## CI ワークフローについて

このリポジトリの CI ワークフローは以下のチェックを実行します:

- **black**: コードフォーマットチェック
- **isort**: import 文のソート順チェック
- **flake8**: Python コードの構文エラーとスタイルチェック
- **pylint**: より詳細な静的解析
- **mypy**: 型チェック
- **py_compile**: Python 構文チェック
- **複数の Python バージョン**: 3.9, 3.10, 3.11, 3.12, 3.13

すべてのチェックが成功すると `all-checks-passed` ジョブが成功し、PR のマージが可能になります。
