# 添加单个员工删除路由
@main.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    flash(f'员工 {employee.name} 已成功删除', 'success')
    return redirect(url_for('main.employees'))

# 添加批量删除路由
@main.route('/employees/batch-delete', methods=['POST'])
@login_required
def batch_delete_employees():
    employee_ids = request.form.getlist('employee_ids')
    if not employee_ids:
        flash('未选择任何员工', 'warning')
        return redirect(url_for('main.employees'))
    
    count = 0
    for id in employee_ids:
        employee = Employee.query.get(id)
        if employee:
            db.session.delete(employee)
            count += 1
    
    db.session.commit()
    flash(f'已成功删除 {count} 名员工', 'success')
    return redirect(url_for('main.employees'))