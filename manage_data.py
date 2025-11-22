from app import app, db, Law, LawVersion, Paragraph
from datetime import date

# --- 1. 数据定义区 ---
# 在这里集中管理所有法律、版本和条文内容。
# 您可以从 buzer.de 等网站复制内容并粘贴到这里。
LAWS_DATA = {
    "EStG": {
        "full_name_de": "Einkommensteuergesetz",
        "full_name_zh": "德国个人所得税法",
        "versions": {
            "2019-01-01": {
                "description": "Fassung für den Veranlagungszeitraum 2019",
                "paragraphs": {
                    "§ 1": {
                        "de": "Natürliche Personen, die im Inland einen Wohnsitz oder ihren gewöhnlichen Aufenthalt haben, sind unbeschränkt einkommensteuerpflichtig.",
                        "zh": "在德国境内有住所或惯常居所的自然人，负有无限个人所得税纳税义务。"
                    },
                    "§ 2": {
                        "de": "(1) Unbeschränkt einkommensteuerpflichtig sind auch deutsche Staatsangehörige, die im Ausland wohnen.",
                        "zh": "（1）居住在国外的德国公民也负有无限所得税义务。"
                    }
                }
            },
            "2020-01-01": {
                "description": "Fassung für den Veranlagungszeitraum 2020",
                "paragraphs": {
                    "§ 1": {
                        "de": "Natürliche Personen, die im Inland einen Wohnsitz oder ihren gewöhnlichen Aufenthalt haben, sind mit all ihren Einkünften unbeschränkt einkommensteuerpflichtig.",
                        "zh": "在德国境内有住所或惯常居所的自然人，其全部所得均负有无限个人所得税纳税义务。"
                    },
                    "§ 2": {
                        "de": "(1) Unbeschränkt einkommensteuerpflichtig sind auch deutsche Staatsangehörige, die im Ausland wohnen und zu einer inländischen juristischen Person des öffentlichen Rechts in einem Dienstverhältnis stehen.",
                        "zh": "（1）居住在国外并与德国公法法人有雇佣关系的德国公民也负有无限所得税义务。"
                    }
                }
            }
        }
    },
    "UStG": {
        "full_name_de": "Umsatzsteuergesetz",
        "full_name_zh": "德国增值税法",
        "versions": {
            "2020-01-01": {
                "description": "Fassung vom 01.01.2020",
                "paragraphs": {
                    "§ 1": {
                        "de": "(1) Der Umsatzsteuer unterliegen die folgenden Umsätze: 1. die Lieferungen und sonstigen Leistungen, die ein Unternehmer im Inland gegen Entgelt im Rahmen seines Unternehmens ausführt.",
                        "zh": "（1）下列交易需缴纳增值税：1. 企业家在其公司框架内在境内有偿提供的交付和服务。"
                    }
                }
            }
        }
    }
}


def clear_and_init_db():
    """清空并重新创建所有数据库表。"""
    print("正在清空并初始化数据库...")
    db.drop_all()
    db.create_all()
    print("数据库已清空并初始化。")

def populate_data_from_structure():
    """
    从 LAWS_DATA 结构中读取数据并填充到数据库中。
    """
    print("开始从数据结构填充数据库...")

    for law_short_name, law_data in LAWS_DATA.items():
        print(f"  - 正在处理法律: {law_short_name}")
        # 创建法律条目
        law_obj = Law(
            short_name=law_short_name,
            full_name_de=law_data['full_name_de'],
            full_name_zh=law_data['full_name_zh']
        )
        db.session.add(law_obj)
        db.session.commit()

        # 遍历该法律的所有版本
        for version_date_str, version_data in law_data['versions'].items():
            version_obj = LawVersion(
                law_id=law_obj.id,
                version_date=date.fromisoformat(version_date_str),
                description=version_data['description']
            )
            db.session.add(version_obj)
            db.session.commit()

            # 遍历该版本下的所有法条
            for p_num, p_content in version_data['paragraphs'].items():
                paragraph_obj = Paragraph(
                    version_id=version_obj.id,
                    paragraph_number=p_num,
                    content_de=p_content['de'],
                    content_zh=p_content.get('zh', '') # 使用 .get 避免中文内容为空时出错
                )
                db.session.add(paragraph_obj)
        db.session.commit()
    print("数据库填充完毕。")


if __name__ == '__main__':
    with app.app_context():
        clear_and_init_db()
        populate_data_from_structure()
    print("\n数据管理脚本执行完毕。")
